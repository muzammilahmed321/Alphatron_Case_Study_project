from io import BytesIO
from pypdf import PdfReader


class PDFParser:
    #Reads a PDF and returns the text of each page.

    def extract_pages(self, file_bytes):
        # Open the PDF from the raw bytes we received
        try:
            reader = PdfReader(BytesIO(file_bytes))
        except Exception:
            raise ValueError("Could not read this PDF")

        pages = []
        page_number = 1

        for page in reader.pages:
            text = page.extract_text() or ""
            text = text.strip()

            # Skip pages with no text (for example, scanned images)
            if text:
                pages.append({"page": page_number, "text": text})

            page_number += 1

        return pages