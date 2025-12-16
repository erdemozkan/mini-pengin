from .utils.pdf_probe import probe_pdf
from .schemas import DocProbe, PageInfo

def build_probe(path: str, max_pages: int = 12) -> DocProbe:
    num_pages, pages = probe_pdf(path, max_pages=max_pages)
    text_pages = sum(1 for p in pages if p.chars > 40)
    ratio = (text_pages / max(1, len(pages)))
    page_infos = [PageInfo(index=p.index, chars=p.chars, images=p.images) for p in pages]
    return DocProbe(num_pages=num_pages, pages=page_infos, text_pages=text_pages, text_page_ratio=ratio)

def route_mode(probe: DocProbe, min_text_ratio: float):
    return "ocr" if probe.text_page_ratio < min_text_ratio else "non_ocr"
