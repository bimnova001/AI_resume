import fitz

def extract_pdf(pdf_path):

    text = ""

    doc = fitz.open(pdf_path)

    for page in doc:
        text += page.get_text()

    return text