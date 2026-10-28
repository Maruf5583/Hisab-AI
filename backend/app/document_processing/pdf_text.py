from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pymupdf


@dataclass
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_type: int


@dataclass
class PageTextResult:
    page_number: int
    width: int
    height: int
    raw_text: str
    blocks: List[TextBlock]
    has_native_text: bool


@dataclass
class PDFTextExtractionResult:
    total_pages: int
    has_native_text: bool
    pages: List[PageTextResult]


def extract_pdf_native_text(pdf_bytes: bytes, min_chars_threshold: int = 15) -> PDFTextExtractionResult:
    """Extract embedded digital text from a PDF file without performing OCR.
    
    If the PDF contains meaningful text (at least min_chars_threshold non-whitespace characters),
    it is marked as having native text.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages_result: List[PageTextResult] = []
    total_non_whitespace_chars = 0

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            rect = page.rect
            width = int(rect.width)
            height = int(rect.height)
            raw_text = page.get_text("text") or ""
            
            # Extract line/text blocks with coordinates
            raw_blocks = page.get_text("blocks") or []
            blocks: List[TextBlock] = []
            for b in raw_blocks:
                # b format: (x0, y0, x1, y1, text, block_no, block_type)
                if len(b) >= 7 and b[6] == 0:  # block_type 0 is text
                    blocks.append(
                        TextBlock(
                            x0=round(b[0], 2),
                            y0=round(b[1], 2),
                            x1=round(b[2], 2),
                            y1=round(b[3], 2),
                            text=b[4].strip(),
                            block_type=b[6],
                        )
                    )

            cleaned_text = "".join(raw_text.split())
            page_chars = len(cleaned_text)
            total_non_whitespace_chars += page_chars

            pages_result.append(
                PageTextResult(
                    page_number=page_idx + 1,
                    width=width,
                    height=height,
                    raw_text=raw_text,
                    blocks=blocks,
                    has_native_text=page_chars >= min_chars_threshold,
                )
            )

        overall_has_native = total_non_whitespace_chars >= min_chars_threshold
        # Normalize individual page flags if overall document has text
        for p in pages_result:
            if not p.has_native_text and overall_has_native and len("".join(p.raw_text.split())) > 0:
                p.has_native_text = True

        return PDFTextExtractionResult(
            total_pages=len(doc),
            has_native_text=overall_has_native,
            pages=pages_result,
        )
    finally:
        doc.close()
