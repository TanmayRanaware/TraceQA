import os
import magic
from typing import Optional
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def extract_text_from_file(file_path: str) -> Optional[str]:
    """Extract text content from various document formats."""
    if not os.path.exists(file_path):
        return None
    
    # Detect file type using python-magic
    file_type = magic.from_file(file_path, mime=True)
    
    if file_type.startswith('text/'):
        return _extract_text_plain(file_path)
    elif file_type == 'application/pdf' and PDF_AVAILABLE:
        return _extract_text_pdf(file_path)
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and DOCX_AVAILABLE:
        return _extract_text_docx(file_path)
    else:
        # Fallback to plain text extraction
        return _extract_text_plain(file_path)


def _extract_text_plain(file_path: str) -> str:
    """Extract text from plain text files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return ""


def _extract_text_pdf(file_path: str) -> str:
    """Extract text from PDF files."""
    if not PDF_AVAILABLE:
        return ""
    
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def _extract_text_docx(file_path: str) -> str:
    """Extract text from DOCX files."""
    if not DOCX_AVAILABLE:
        return ""
    
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting DOCX text: {str(e)}"


def get_supported_formats() -> list:
    """Get list of supported document formats."""
    formats = ["text/plain"]
    if PDF_AVAILABLE:
        formats.append("application/pdf")
    if DOCX_AVAILABLE:
        formats.append("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    return formats
