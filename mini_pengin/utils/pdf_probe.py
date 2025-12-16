from dataclasses import dataclass
import fitz

@dataclass
class PageCheck:
    index: int
    chars: int
    images: int

def probe_pdf(path: str, max_pages: int = 12):
    doc = fitz.open(path)
    n = len(doc)
    step = max(1, n // max_pages)
    pages = []
    for i in range(0, n, step):
        if len(pages) >= max_pages: break
        p = doc[i]
        txt = p.get_text("text") or ""
        imgs = len(p.get_images(full=True))
        pages.append(PageCheck(index=i, chars=len(txt), images=imgs))
    doc.close()
    return n, pages
