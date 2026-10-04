"""
Resume document parsing for SmartEscrow.

Extracts plain text from uploaded resume files (PDF, DOCX, TXT/MD) using
free, local libraries — no external API or cost. The extracted text feeds the
AI skill-extraction and job-matching pipeline in ai.py.
"""
from __future__ import annotations

import io


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            return _from_pdf(data)
        if name.endswith(".docx"):
            return _from_docx(data)
        # txt, md, or anything else: best-effort decode.
        return data.decode("utf-8", errors="ignore")
    except Exception:
        # Fall back to a lenient decode so the user is never hard-blocked.
        return data.decode("utf-8", errors="ignore")


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def _from_docx(data: bytes) -> str:
    import docx

    document = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs).strip()
