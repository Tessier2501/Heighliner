from __future__ import annotations

"""
功能: 读取同目录下 PDF, 找到包含 '价税合计' 的一行的金额与包含 '发票号码' 的一行的号码,
并将文件重命名为 "<前缀>_<金额>_<发票号码>.pdf", 输出重命名结果.
"""

import re
from decimal import Decimal
from pathlib import Path

import pdfplumber


PLACEHOLDER_PREFIX = "313977704179" # 将此替换为你的前缀
AMOUNT_PATTERN = re.compile(r"价税合计.*?¥\s*([0-9,]+(?:\.[0-9]+)?)")
INVOICE_PATTERN = re.compile(r"(?:发+票+号+码+)+[:：]+\s*(\d+)")
TOTAL_HEADER_PATTERN = re.compile(r"合+\s*计+")
LINE_AMOUNT_PATTERN = re.compile(r"[¥￥]\s*([0-9,]+(?:\.[0-9]+)?)")


def extract_amount_from_text(text: str) -> str | None:
    """在文本中查找包含 '价税合计' 的行, 返回首个 '¥' 后的金额."""

    for line in text.splitlines():
        match = AMOUNT_PATTERN.search(line)
        if match:
            return match.group(1)
    return None


def extract_amount_from_pdf(pdf_path: Path) -> str | None:
    """按页提取文本, 返回首个匹配金额的结果."""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            amount = extract_amount_from_text(text)
            if amount:
                return amount
    return None


def extract_two_amounts_after_total(text: str) -> list[str] | None:
    """在出现 '合 计' (允许重复字与空格) 的行之后, 抓取后续行中的两个金额."""

    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if not TOTAL_HEADER_PATTERN.search(line):
            continue
        window = lines[idx : idx + 10]  # include header line; look ahead up to 9 lines
        found: list[str] = []
        for tail in window:
            for m in LINE_AMOUNT_PATTERN.finditer(tail):
                found.append(m.group(1))
                if len(found) == 2:
                    return found
        return found if found else None
    return None


def extract_two_amounts_after_total_from_pdf(pdf_path: Path) -> list[str] | None:
    """按页查找 '合 计' 之后的两个金额, 返回列表长度为 2 的数字字符串."""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            res = extract_two_amounts_after_total(text)
            if res:
                return res
    return None


def extract_invoice_from_text(text: str) -> str | None:
    """在文本中查找包含 '发票号码' 的行, 返回其后的号码."""

    for line in text.splitlines():
        match = INVOICE_PATTERN.search(line)
        if match:
            return match.group(1)
    return None


def extract_invoice_from_pdf(pdf_path: Path) -> str | None:
    """按页提取文本, 返回首个匹配发票号码的结果."""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            invoice = extract_invoice_from_text(text)
            if invoice:
                return invoice
    return None


def sanitize_label(label: str) -> str:
    """清理文件名中的不安全字符, 替换为下划线."""

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", label.strip())
    return cleaned.strip("._") or "UNNAMED"


def next_available_target(pdf_path: Path, base_label: str) -> Path:
    """生成可用的新文件名, 若重名则递增后缀."""

    base = sanitize_label(base_label)
    candidate = pdf_path.with_name(f"{base}.pdf")
    counter = 1
    while candidate.exists():
        candidate = pdf_path.with_name(f"{base}_{counter}.pdf")
        counter += 1
    return candidate


def rename_pdf(pdf_path: Path, label: str) -> Path:
    """执行重命名并返回新路径 (包含重名处理)."""

    target = next_available_target(pdf_path, label)
    pdf_path.rename(target)
    return target


def process_pdf(pdf_path: Path) -> None:
    """处理单个 PDF: 提取金额、发票号码, 校验合计行, 重命名并打印结果."""

    amount = extract_amount_from_pdf(pdf_path)
    invoice = extract_invoice_from_pdf(pdf_path)
    two_amounts = extract_two_amounts_after_total_from_pdf(pdf_path)

    if not amount or not invoice or not two_amounts or len(two_amounts) < 2:
        missing = []
        if not amount:
            missing.append("amount")
        if not invoice:
            missing.append("invoice")
        if not two_amounts or len(two_amounts) < 2:
            missing.append("sum_parts")
        print(f"Skipped (missing {', '.join(missing)}): {pdf_path.name}")
        return

    def to_decimal(val: str) -> Decimal:
        return Decimal(val.replace(",", ""))

    total_expected = to_decimal(amount)
    part_sum = to_decimal(two_amounts[0]) + to_decimal(two_amounts[1])

    if (part_sum - total_expected).copy_abs() > Decimal("0"):
        print(
            f"Skipped (sum mismatch): {pdf_path.name} | parts={part_sum} vs total={total_expected}"
        )
        return

    amount_clean = amount.replace(",", "")
    label = f"{PLACEHOLDER_PREFIX}_{amount_clean}_{invoice}"
    new_path = rename_pdf(pdf_path, label)
    print(f"Renamed: {pdf_path.name} -> {new_path.name}")


def main() -> None:
    """遍历脚本所在目录的 PDF 并逐个处理."""

    script_dir = Path(__file__).resolve().parent
    pdf_files = sorted(script_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in current directory.")
        return

    for pdf_file in pdf_files:
        process_pdf(pdf_file)


if __name__ == "__main__":
    main()