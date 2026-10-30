"""
@Author:xuyinglai
@Date:2026/10/30
@DESC:
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def split_pdf(
    pdf_path: str,
    output_dir: str,
    max_pages: int = 150,
    max_bytes: int = 180 * 1024 * 1024,
) -> list[Path]:
    """
    按原始页序拆分 PDF：
    1. 每份最多 max_pages 页；
    2. 每份最多 max_bytes 字节；
    3. 如果某一页单独导出仍然超限，明确报错。
    """
    if max_pages <= 0 or max_bytes <= 0:
        raise ValueError("页数和文件大小限制必须大于 0")

    source = Path(pdf_path)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    result: list[Path] = []

    with source.open("rb") as source_file:
        reader = PdfReader(source_file)

        if reader.is_encrypted:
            raise ValueError("请先解密 PDF，再上传")

        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("PDF 没有可解析的页面")

        def write_range(start: int, end: int):
            # start 包含，end 不包含。
            # 文件名使用人习惯的页码，从 1 开始。
            part_path = target_dir / (
                f"pages_{start + 1:06d}_{end:06d}.pdf"
            )

            writer = PdfWriter()
            try:
                writer.append(
                    reader,
                    pages=(start, end),
                    import_outline=False,
                )
                with part_path.open("wb") as output:
                    writer.write(output)
            finally:
                writer.close()

            if part_path.stat().st_size <= max_bytes:
                result.append(part_path)
                return

            # 页数合格，但字节大小超限，需要继续拆小。
            part_path.unlink()

            if end - start == 1:
                raise ValueError(
                    f"PDF 第 {start + 1} 页单独导出仍超过大小限制，"
                    "需要先压缩这一页的图片"
                )

            middle = (start + end) // 2
            write_range(start, middle)
            write_range(middle, end)

        for start in range(0, page_count, max_pages):
            end = min(start + max_pages, page_count)
            write_range(start, end)

    return result