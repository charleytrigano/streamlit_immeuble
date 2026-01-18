import re
from pypdf import PdfReader
from datetime import datetime

def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    return " ".join(page.extract_text() or "" for page in reader.pages)

def extract_amount(text):
    matches = re.findall(r"(\d+[ \d]*[,\.]\d{2})", text)
    if matches:
        return float(matches[-1].replace(" ", "").replace(",", "."))
    return None

def extract_date(text):
    matches = re.findall(r"\d{2}/\d{2}/\d{4}", text)
    if matches:
        try:
            return datetime.strptime(matches[0], "%d/%m/%Y").date()
        except:
            pass
    return None

