import base64
from typing import Any

import fitz  # pymupdf


def extract_text_from_input(task_input: dict[str, Any]) -> str | None:
    """Extract text content from various input formats."""
    if "text" in task_input:
        print(f"Found text directly in input ({len(task_input['text'])} chars)")
        return str(task_input["text"])

    if "content" in task_input:
        print(f"Found text in 'content' field ({len(task_input['content'])} chars)")
        return str(task_input["content"])

    if "file_content" in task_input:
        return _extract_from_file_content(task_input["file_content"])

    return None


def _extract_from_file_content(file_content: str) -> str:
    """Decode and extract text from base64 file content (PDF or text)."""
    binary_content = base64.b64decode(file_content)
    print(f"Decoded base64 content ({len(binary_content)} bytes)")

    # Try to parse as PDF first
    try:
        with fitz.open(stream=binary_content, filetype="pdf") as pdf_doc:
            text_parts = [page.get_text() for page in pdf_doc]

        text_content = "\n\n".join(text_parts)
        print(f"Extracted text from PDF ({len(text_parts)} pages, {len(text_content)} chars)")
        return text_content

    except Exception as pdf_error:
        # Not a PDF or PDF parsing failed, try as plain text
        return _decode_text_content(binary_content, pdf_error)


def _decode_text_content(binary_content: bytes, original_error: Exception) -> str:
    """Try to decode binary content as text using various encodings."""
    for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            text_content = binary_content.decode(encoding)
            print(f"Decoded as {encoding} ({len(text_content)} chars)")
            return text_content
        except UnicodeDecodeError:
            continue

    msg = f"Could not decode file content. Not a valid PDF or text file. Error: {original_error}"
    raise ValueError(msg) from original_error
