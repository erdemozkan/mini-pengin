import fitz
def extract_text_pymupdf(path: str):
    d = fitz.open(path)
    out = [(p.get_text("text") or "") for p in d]
    d.close()
    return out
