import pdfplumber
from pathlib import Path

def dump_pdf_lines(pdf_path: Path):
    print("=" * 80)
    print(f"FILE: {pdf_path.name}")
    print("=" * 80)

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            print(f"\n--- Page {page_index + 1} ---")

            text = page.extract_text() or ""
            lines = text.splitlines()

            if not lines:
                print("(No text content extracted)")
                continue

            print(f"Total lines: {len(lines)}")

            for i, line in enumerate(lines, start=1):
                print(f"[{i:04d}] {line}")


def main():
    # Use the script's directory instead of the current working directory to
    # avoid missing PDFs when launched from elsewhere.
    script_dir = Path(__file__).resolve().parent
    pdf_files = sorted(script_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in current directory.")
        return

    for pdf_file in pdf_files:
        dump_pdf_lines(pdf_file)


if __name__ == "__main__":
    main()