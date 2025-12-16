import argparse, os, sys, concurrent.futures, json
from .config import ForgeConfig
from .forge_runner import run_on_pdf
from .ingest_io import iter_pdf_paths

def main():
    ap = argparse.ArgumentParser(description="mini-pengin (macOS)")
    ap.add_argument("--input", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ocr", choices=["auto","tesseract","deepseek","off"], default="auto")
    ap.add_argument("--ocr-lang", default=None)
    ap.add_argument("--deepseek-prompt", choices=["markdown","plain"], default="markdown")
    ap.add_argument("--text-engine", choices=["pymupdf","docling"], default="pymupdf")
    ap.add_argument("--lang-detector", choices=["auto","off"], default="auto")
    ap.add_argument("--min-text-perc", type=float, default=0.55)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--save-pages", action="store_true")
    ap.add_argument("--keep-jsonl", action="store_true")
    ap.add_argument("--tables", choices=["auto","docling","camelot","off"], default="auto")
    a = ap.parse_args()
    cfg = ForgeConfig(min_text_page_ratio=a.min_text_perc, ocr_engine=a.ocr, ocr_lang=a.ocr_lang, deepseek_prompt=a.deepseek_prompt,
                      text_engine=a.text_engine, lang_detector=a.lang_detector, save_pages=a.save_pages, keep_jsonl=a.keep_jsonl,
                      workers=a.workers, tables=a.tables)
    os.makedirs(a.out, exist_ok=True)
    pdfs = list(iter_pdf_paths(a.input))
    if not pdfs: print("No PDFs found.", file=sys.stderr); sys.exit(2)
    results=[]; 
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        futs=[ex.submit(run_on_pdf, p, a.out, cfg) for p in pdfs]
        for f in concurrent.futures.as_completed(futs):
            try: results.append(f.result())
            except Exception as e: print(f"[ERR] {e}", file=sys.stderr)
    print(json.dumps(results, indent=2))
if __name__ == "__main__": main()
