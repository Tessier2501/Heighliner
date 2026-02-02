"""
用法:
    cd <脚本所在目录>
    python watcher.py

假设目录结构 (脚本所在目录):
    0_incoming/      <- 浏览器下载到此 (人工改名为 <订单号>.pdf)
    1_processing/
    2_processed/
    3_failed/
    rename_invoice.py <- 现有的解析/重命名脚本, 需与本脚本同目录

说明:
- 只处理后缀严格为 .pdf 的文件 (避免下载中被处理)
- 要求文件名 (不含扩展) 为纯数字且长度在 10~20 之间 (可根据需要调整)
- 本脚本不会改变 rename_invoice.py 的内部逻辑, 只设置其 PLACEHOLDER_PREFIX 并调用 process_pdf()
"""

from __future__ import annotations
import time
import shutil
import traceback
from pathlib import Path
import re
import sys
import importlib

# ---------- 配置 ----------
POLL_INTERVAL    = 2.0  # 秒
ORDER_ID_PATTERN = re.compile(r"^\d{10,20}$")  # 文件名必须满足此规则 (仅数字, 长度 10-20)

# ---------- 目录与后缀 ----------
SCRIPT_DIR      = Path(__file__).resolve().parent
INCOMING_DIR    = SCRIPT_DIR / "0_incoming"
PROCESSING_DIR  = SCRIPT_DIR / "1_processing"
PROCESSED_DIR   = SCRIPT_DIR / "2_processed"
FAILED_DIR      = SCRIPT_DIR / "3_failed"
TEMP_SUFFIXES   = (".crdownload", ".part", ".tmp", ".download")

# ---------- 校验与文件操作 ----------
for d in (INCOMING_DIR, PROCESSING_DIR, PROCESSED_DIR, FAILED_DIR):
    d.mkdir(parents=True, exist_ok=True)

def is_valid_order_filename(p: Path) -> bool:
    """判断 incoming 中的 pdf 文件名 (不含扩展) 是否满足订单号格式."""
    return bool(ORDER_ID_PATTERN.match(p.stem))

def safe_move(src: Path, dst_dir: Path) -> Path:
    """把 src 移动到 dst_dir, 返回目标路径 (若存在会覆盖失败地名)."""
    dst = dst_dir / src.name
    # 如果目标已存在, 给出唯一后缀
    if dst.exists():
        base = dst.stem
        suffix = dst.suffix
        counter = 1
        while True:
            candidate = dst_dir / f"{base}_{counter}{suffix}"
            if not candidate.exists():
                dst = candidate
                break
            counter += 1
    # 使用 shutil.move 以兼容不同磁盘分区
    shutil.move(str(src), str(dst))
    return dst

def mark_failed_and_move(src: Path, reason: str) -> Path:
    """把文件移动到 failed, 并在文件名加入失败原因与时间戳, 返回新路径."""
    safe_name = src.stem
    # 限制 reason 简短且无危险字符
    reason_clean = re.sub(r"[^A-Za-z0-9_-]", "_", reason)[:40]
    new_name = f"{safe_name}__FAILED__{reason_clean}{src.suffix}"
    dst = FAILED_DIR / new_name
    # 若已存在则 append counter
    counter = 1
    while dst.exists():
        dst = FAILED_DIR / f"{safe_name}__FAILED__{reason_clean}_{counter}{src.suffix}"
        counter += 1
    shutil.move(str(src), str(dst))
    return dst

def find_renamed_output_for_order(order_id: str) -> list[Path]:
    """
    在 processing 目录查找 process_pdf 生成的以 <order_id>_ 开头的文件 (可能存在多个, 返回列表).
    这是基于 rename_invoice.py 中使用 PLACEHOLDER_PREFIX 来生成文件名的约定.
    """
    pattern = f"{order_id}_"
    return sorted(p for p in PROCESSING_DIR.iterdir() if p.name.startswith(pattern) and p.suffix.lower() == ".pdf")

def is_temp_download(p: Path) -> bool:
    """判断是否为浏览器临时下载文件 (按常见后缀)."""
    name = p.name.lower()
    return any(name.endswith(suf) for suf in TEMP_SUFFIXES)

def wait_until_stable(p: Path, interval: float = 0.5, checks: int = 2) -> bool:
    """等待文件在连续检查间隔内大小/mtime 不变, 避免抢占下载中."""
    try:
        prev = p.stat()
    except FileNotFoundError:
        return False
    for _ in range(checks):
        time.sleep(interval)
        try:
            cur = p.stat()
        except FileNotFoundError:
            return False
        if cur.st_size == prev.st_size and cur.st_mtime == prev.st_mtime:
            return True
        prev = cur
    return False

def main_loop():
    print("Watcher started. Polling:", INCOMING_DIR)
    # 动态导入的脚本 (确保文件名正确)
    try:
        # 动态导入避免 IDE 报缺少包; 真实错误仍会在运行时抛出
        renamer = importlib.import_module("rename_invoice")  # type: ignore[import-not-found]
    except Exception as e:
        print("ERROR: failed to import rename_invoice.py:", e)
        sys.exit(1)

    while True:
        try:
            pdfs = sorted(INCOMING_DIR.glob("*.pdf"))
            if not pdfs:
                time.sleep(POLL_INTERVAL)
                continue

            # 逐个处理 (串行)
            for incoming_file in pdfs:
                print("\nDetected:", incoming_file.name)

                # 只处理严格的 .pdf (浏览器下载中的不满足)
                if incoming_file.suffix.lower() != ".pdf":
                    print("  Skip (not .pdf):", incoming_file.name)
                    continue

                if is_temp_download(incoming_file):
                    print("  Skip (temp download suffix):", incoming_file.name)
                    continue

                if not wait_until_stable(incoming_file):
                    print("  Skip (file not stable yet):", incoming_file.name)
                    continue

                # 先尝试把文件移动到 processing (原子性取决于文件系统)
                try:
                    processing_file = safe_move(incoming_file, PROCESSING_DIR)
                except Exception as e:
                    print("  ERROR: failed to move to processing:", e)
                    continue

                order_id = processing_file.stem  # 期望为订单号
                if not is_valid_order_filename(processing_file):
                    print(f"  Bad filename (order id invalid): {processing_file.name}")
                    # 移到 failed, 并带上 BAD_FILENAME 标注
                    mark_failed_and_move(processing_file, "BAD_FILENAME")
                    # 继续处理目录中下一文件
                    continue

                # 将订单号设置为 rename_invoice 中的前缀 (脚本会用它来命名输出文件)
                try:
                    renamer.PLACEHOLDER_PREFIX = order_id
                except Exception:
                    # 如果 rename_invoice 没有该变量, 我们仍然调用 process_pdf
                    print("  WARNING: couldn't set PLACEHOLDER_PREFIX on rename_invoice module. Continuing...")

                # 调用现有的处理函数
                try:
                    print(f"  Processing (order={order_id}) ...")
                    # process_pdf 以 pdf_path 为参数并负责重命名原始文件到 <order>_<amount>_<invoice>.pdf
                    renamer.process_pdf(processing_file)
                except Exception as exc:
                    # 任意异常 -> 标注失败并移动
                    tb = traceback.format_exc()
                    print(f"  ERROR: process_pdf raised exception for {processing_file.name}: {exc}")
                    print(tb)
                    # 把 processing_file 移到 failed 并包含异常简述 (截断)
                    mark_failed_and_move(processing_file, "EXC")
                    continue

                # 处理完成后: 寻找以 order_id_ 开头的输出文件 (应由 process_pdf 生成)
                outputs = find_renamed_output_for_order(order_id)
                if outputs:
                    # 将所有匹配的输出移动到 processed (通常只有一个)
                    for out in outputs:
                        # 目标名可能已存在于 processed, safe_move 会确保不覆盖
                        print("  Moving processed:", out.name)
                        safe_move(out, PROCESSED_DIR)
                    print(f"  Done (moved {len(outputs)} file(s) to processed).")
                else:
                    # 没有生成命名文件 -> 认为该文件被 skipped (process_pdf 会 print 原因)
                    print(f"  No renamed output found for order {order_id} — moving to failed.")
                    mark_failed_and_move(processing_file, "NO_RENAMED_OUTPUT")

            # 轮询等待
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nWatcher stopped by user.")
            break
        except Exception:
            print("Unexpected error in watcher loop:")
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main_loop()
