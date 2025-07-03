from docx import Document
import json, sys

def generate_docx(meta, paragraphs, output_path):
    doc = Document()
    doc.add_heading("Judgment Metadata", level=1)
    for key, val in meta.items():
        doc.add_paragraph(f"{key.title()}: {val}")
    
    doc.add_heading("Judgment Text", level=1)
    for para in paragraphs:
        doc.add_paragraph(para)

    doc.save(output_path)

if __name__ == "__main__":
    meta = json.loads(open(sys.argv[1]).read())
    paragraphs = json.loads(open(sys.argv[2]).read())
    output_path = sys.argv[3]
    generate_docx(meta, paragraphs, output_path)
