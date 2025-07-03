import sys
import re
import spacy
import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

nlp = spacy.load("en_core_web_sm")

def extract_metadata(text, field):
    field = field.lower()

    if field == "citationyear":
        match = re.search(r'NEUTRAL CITATION NO\.\s*(\d{4}):', text)
        return match.group(1) if match else "Not found"

    elif field == "neutralcitation":
        match = re.search(r'NEUTRAL CITATION NO\.\s*([^\n]+)', text)
        return match.group(1).strip() if match else "Not found"

    elif field == "judge":
        judges = re.findall(r'JUSTICE\s+[A-Z\s]+', text, flags=re.IGNORECASE)
        return "; ".join(judges) if judges else "Not found"

    elif field == "courtname":
        # Find the first line containing 'COURT' (case-insensitive)
        court_lines = re.findall(r'.*court.*', text, flags=re.IGNORECASE)
        if court_lines:
            return court_lines[0].strip()
        else:
            return "Unknown court"

    elif field == "party":
        doc = nlp(text)
        parties = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "PERSON")]
        return ", ".join(parties[:5]) if parties else "Not found"

    return f"Field '{field}' not supported"

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

def extract_text_from_pdf_with_pdfplumber(pdf_path):
    output_txt = "output.txt"   # Output text file
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            # You can tweak x_tolerance and y_tolerance for better results
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                all_text += text + "\n\n"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(all_text)

    return all_text

def extract_text_from_pdf_with_ocr(pdf_path):
    output_txt = "output_ocr.txt"
    pages = convert_from_path(pdf_path)
    all_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page, lang='eng')
        all_text += text + "\n\n"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(all_text)

    return all_text

if __name__ == "__main__":
    file_path = sys.argv[1]
    field_name = sys.argv[2]

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".txt":
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                text = f.read()
    else:
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as f:
                text = f.read()
    result = extract_metadata(text, field_name)
    print(result)
