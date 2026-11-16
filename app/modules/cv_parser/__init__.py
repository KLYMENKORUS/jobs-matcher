__all__ = ("CVParser",)

import asyncio
import re
import typing as t
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.shared.utils.exceptions.domains.users import (
    CVParsingError,
    UnsupportedCVFormatError,
)


class CVParser:
    """
    Extracts plain text from a CV file (PDF, DOCX, TXT) for the analysis.

    The libraries are synchronous, so parsing runs in a thread to keep the
    event loop free.
    """
    SUPPORTED_EXTENSIONS: t.Final[tuple[str, ...]] = (".pdf", ".docx", ".txt")

    @classmethod
    def ensure_supported(cls, *, filename: str) -> str:
        """Returns the lower-cased extension or raises for an unsupported file."""
        extension: str = Path(filename).suffix.lower()
        if extension not in cls.SUPPORTED_EXTENSIONS:
            raise UnsupportedCVFormatError(
                filename=filename, supported=cls.SUPPORTED_EXTENSIONS
            )
        return extension

    async def parse(self, *, path: Path) -> str:
        return await asyncio.to_thread(self._parse, path)

    def _parse(self, path: Path) -> str:
        extension: str = self.ensure_supported(filename=path.name)
        if not path.is_file():
            raise CVParsingError(path=path, reason="file not found")

        try:
            match extension:
                case ".pdf":
                    text = self._parse_pdf(path)
                case ".docx":
                    text = self._parse_docx(path)
                case _:
                    text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise CVParsingError(path=path, reason=repr(exc)) from exc

        if not (text := self._normalize(text)):
            raise CVParsingError(path=path, reason="no text extracted")

        return text

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _parse_docx(path: Path) -> str:
        document = Document(str(path))
        lines: list[str] = [paragraph.text for paragraph in document.paragraphs]

        for table in document.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text.strip() for cell in row.cells))

        return "\n".join(lines)

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()
