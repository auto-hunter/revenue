from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pypdfium2 as pdfium
from PIL import Image, ImageOps


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class DocumentParseError(ValueError):
    pass


@dataclass
class DocumentPage:
    source_file: str
    page_number: int
    image: Image.Image


def parse_document(uploaded_file: BinaryIO) -> list[DocumentPage]:
    """Convert an uploaded PDF or image into normalized page images."""
    filename = getattr(uploaded_file, "name", "uploaded_file")
    extension = Path(filename).suffix.lower()
    raw_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()

    try:
        if extension == ".pdf":
            pdf = pdfium.PdfDocument(raw_bytes)
            pages = []
            for index in range(len(pdf)):
                image = pdf[index].render(scale=2).to_pil().convert("RGB")
                pages.append(DocumentPage(filename, index + 1, image))
            if not pages:
                raise DocumentParseError("PDF에 페이지가 없습니다.")
            return pages

        if extension in SUPPORTED_IMAGE_EXTENSIONS:
            image = Image.open(BytesIO(raw_bytes))
            image = ImageOps.exif_transpose(image).convert("RGB")
            return [DocumentPage(filename, 1, image)]
    except DocumentParseError:
        raise
    except Exception as exc:
        raise DocumentParseError(f"파일을 읽을 수 없습니다: {exc}") from exc

    raise DocumentParseError(f"지원하지 않는 파일 형식입니다: {extension or '확장자 없음'}")
