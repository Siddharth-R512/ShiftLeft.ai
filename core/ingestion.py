import fitz
import logging
from docx import Document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s -%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SAMPLE_PDF_PATH = ""
SAMPLE_DOCX_PATH = ""

def pdf_to_text(file):
    """Extract content from a PDF file with error handling"""
    plain_text = ""
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page_num, page in enumerate(doc):
                try:
                    plain_text += page.get_text()
                except Exception as e:
                    logger.warning(f"Failed to extract text from page no. {page_num}")
                    continue
        return plain_text if plain_text.strip() else "Unable to extract text from PDF"
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return f"Error reading from PDF: {str(e)}"

def docx_to_text(file):
    """Extract content from a DOCX file with error handling"""
    try:
        doc = Document(file)
        plain_text = ""
        for para in doc.paragraphs:
            plain_text += para.text + "\n"
        return plain_text if plain_text.strip() else "Unable to extract text from DOCX"
    except Exception as e:
        logger.error(f"DOCX Extraction error: {str(e)}")
        return f"Error reading DOCX: {str(e)}"
    
def txt_to_text(file):
    """Extract content from TXT file with error handling"""
    file.seek(0)
    try:
        return file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file.read().decode("latin-1")
        except Exception as e:
            logger.error(f"TXT extraction error: {str(e)}")
            return f"Error reading TXT: {str(e)}"


# 1. PDF Ingestion
# 2. Word doc ingestion
# 3. Plain text ingestion
