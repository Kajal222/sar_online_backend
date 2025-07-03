import fitz  # PyMuPDF
import sys, os
import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import nltk
from nltk.corpus import words

# Ensure the word list is downloaded (run once)
try:
    english_words = set(words.words())
except LookupError:
    nltk.download('words')
    english_words = set(words.words())

def normalize_word(word):
    # Reduce repeated letters to a single letter
    normalized = re.sub(r'(\w)\1+', r'\1', word)
    return normalized

def dictionary_normalize_text(text):
    def process_word(word):
        # Remove punctuation for dictionary check
        word_alpha = re.sub(r'[^a-zA-Z]', '', word)
        if word_alpha.lower() in english_words:
            return word
        norm = normalize_word(word_alpha)
        # Re-attach original punctuation if needed
        if norm.lower() in english_words:
            return norm
        return word
    # Process each word in the text
    return ' '.join(process_word(w) for w in text.split())

def clean_text(text):
    # Remove headers/footers, junk chars
    lines = text.split('\n')
    cleaned = [line.strip() for line in lines if len(line.strip()) > 2]
    return '\n'.join(cleaned)

def extract_text_pdfplumber(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if text:
                    all_text += text + "\n\n"
        return all_text.strip()
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        return ""

def extract_text_fitz(filepath):
    try:
        doc = fitz.open(filepath)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text.strip()
    except Exception as e:
        print(f"fitz failed: {e}")
        return ""

def extract_text_ocr(filepath):
    try:
        pages = convert_from_path(filepath)
        all_text = ""
        for page in pages:
            text = pytesseract.image_to_string(page, lang='eng')
            all_text += text + "\n\n"
        return all_text.strip()
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""

def main(filepath):
    # Try pdfplumber first
    text = extract_text_pdfplumber(filepath)
    if not text or len(text) < 20:
        # Fallback to fitz
        text = extract_text_fitz(filepath)
    if not text or len(text) < 20:
        # Fallback to OCR
        text = extract_text_ocr(filepath)
    if not text:
        print("Failed to extract text from PDF.")
        sys.exit(1)
    cleaned = clean_text(text)
    normalized = dictionary_normalize_text(cleaned)
    # Save cleaned text as .txt file in the same directory as the PDF
    base, _ = os.path.splitext(filepath)
    txt_path = base + ".txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(normalized)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <pdf_file_path>")
        sys.exit(1)
    main(sys.argv[1])