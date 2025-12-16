import os
from dataclasses import asdict
from typing import List, Dict
from .config import ForgeConfig
from .schemas import DocBundle
from . import ingest_io
from .route_scangate import build_probe, route_mode
from .extractors.ink_extractor import extract_text_pymupdf
from .postprocess.paraweld import ParaWeld
from .postprocess.marklist_normalizer import MarklistNormalizer
from .postprocess.page_tag_wiper import PageTagWiper
from .postprocess.boiler_skim import BoilerSkim
from .postprocess.tongue_tag import TongueTagger
from .postprocess.token_meter import TokenMeter

try:
    from .extractors.deepseek_extractor import ocr_pages_deepseek
except Exception:
    ocr_pages_deepseek = None

from .tables.docling_tables import extract_tables_docling
from .tables.ocr_md_tables import extract_tables_from_markdown_pages
from .tables.camelot_tables import extract_tables_camelot


def _ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def _concat_with_offsets(pages: List[str]):
    offs = []
    cur = 0
    for p in pages:
        offs.append(cur)
        cur += len(p)
    return "".join(pages), offs


def _score_csv_table(csv_path: str) -> float:
    """
    Lightweight table quality score to compare CSVs:
      score ~ (rows * cols) / (1 + 10 * empty_fraction)
    Falls back to 0.0 if pandas or file load fails.
    """
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        if df.empty:
            return 0.0
        r, c = df.shape
        empties = df.isna().mean().mean()
        return (r * c) / (1.0 + 10.0 * float(empties))
    except Exception:
        return 0.0


def run_on_pdf(path: str, outdir: str, cfg: ForgeConfig) -> Dict:
    doc_id = ingest_io.sha256_of_file(path)[:16]

    # Router (OCR vs non-OCR)
    probe = build_probe(path, max_pages=cfg.max_pages_probe)
    routed_choice = route_mode(probe, min_text_ratio=cfg.min_text_page_ratio)
    use_ocr = (routed_choice == "ocr")
    route_reason = f"router_{routed_choice}"

    # Honor CLI flags / availability
    if cfg.ocr_engine == "off":
        use_ocr = False
        route_reason = "ocr_disabled_by_flag"
    elif cfg.ocr_engine == "deepseek":
        if ocr_pages_deepseek is None:
            use_ocr = False
            route_reason = "deepseek_missing"
        else:
            use_ocr = True
            route_reason = "forced_deepseek"
    elif cfg.ocr_engine == "tesseract":
        # In this build we reuse DeepSeek wrapper for OCR; if missing, skip OCR.
        if ocr_pages_deepseek is None:
            use_ocr = False
            route_reason = "tesseract_unavailable"
        else:
            use_ocr = True
            route_reason = "tesseract_unavailable_used_deepseek"
    else:
        if use_ocr and ocr_pages_deepseek is None:
            use_ocr = False
            route_reason = "ocr_engine_missing"

    # Extract text
    page_markdowns = None
    if use_ocr:
        pages = ocr_pages_deepseek(path, prompt_mode=cfg.deepseek_prompt) if ocr_pages_deepseek else extract_text_pymupdf(path)
        routed = "ocr"
        if cfg.deepseek_prompt == "markdown":
            page_markdowns = pages[:]
    else:
        pages = extract_text_pymupdf(path)
        routed = "non_ocr"

    # 4) Tables (do early on the original PDF / OCR markdown)
    table_meta = {"engine": None, "count": 0, "items": []}
    tdir = os.path.join(outdir, doc_id, "tables")

    if cfg.tables != "off":
        if cfg.tables == "camelot":
            # Explicit Camelot mode, regardless of route
            table_meta = extract_tables_camelot(path, tdir)

        elif cfg.tables == "docling":
            # Docling only
            try:
                table_meta = extract_tables_docling(path, tdir)
            except Exception as e:
                table_meta = {"engine": "docling", "error": str(e), "count": 0, "items": []}

        elif cfg.tables == "auto":
            # Docling first
            try:
                table_meta = extract_tables_docling(path, tdir)
            except Exception as e:
                table_meta = {"engine": "docling", "error": str(e), "count": 0, "items": []}

            # If Docling found nothing and we have OCR markdown pages, try MD parser
            if table_meta.get("count", 0) == 0 and routed == "ocr" and page_markdowns and cfg.deepseek_prompt == "markdown":
                md_meta = extract_tables_from_markdown_pages(page_markdowns, tdir)
                if md_meta.get("count", 0) > 0:
                    table_meta = md_meta

            # If still nothing, try Camelot as last resort
            if table_meta.get("count", 0) == 0:
                cm = extract_tables_camelot(path, tdir)
                if cm.get("count", 0) > 0:
                    table_meta = cm

    # Compute a simple "best table" score (optional, helpful for benchmarking)
    try:
        best_csv, best_score = None, 0.0
        for it in table_meta.get("items", []):
            csv = it.get("path_csv")
            if not csv:
                continue
            s = _score_csv_table(csv)
            if s > best_score:
                best_score, best_csv = s, csv
        if best_csv:
            table_meta["best_csv"] = best_csv
            table_meta["best_score"] = round(best_score, 3)
    except Exception:
        pass

    # 5) Pre/Post chain
    wiper = PageTagWiper()
    skimmer = BoilerSkim()
    welder = ParaWeld()
    marker = MarklistNormalizer()

    pages = wiper.strip_headers_footers(pages, 2, 2, 0.45, 3)
    pages = skimmer.drop(pages)
    pages = [welder.fuse(p) for p in pages]
    pages = [marker.normalize(p) for p in pages]
    text, page_offsets = _concat_with_offsets([wiper.remove_page_labels(p) for p in pages])

    # Lang + tokens
    tongue = TongueTagger() if cfg.lang_detector == "auto" else None
    language = tongue.guess(text) if tongue else None
    meter = TokenMeter()
    token_count = meter.count(text)

    bundle = DocBundle(
        doc_id=doc_id,
        text=text,
        page_slices=pages,
        page_offsets=page_offsets,
        routed=routed,
        language=language or "unknown",
        meta={
            "probe": {
                "num_pages": probe.num_pages,
                "text_page_ratio": probe.text_page_ratio,
                "text_pages_sampled": probe.text_pages,
            },
            "route_reason": route_reason,
            "token_count": token_count,
            "tables": table_meta,
        },
    )

    # Write outputs
    base = os.path.join(outdir, doc_id)
    _ensure_dir(base)
    ingest_io.write_text(os.path.join(base, "text.txt"), text)

    if cfg.save_pages:
        pdir = os.path.join(base, "page_text")
        _ensure_dir(pdir)
        for i, p in enumerate(pages, 1):
            ingest_io.write_text(os.path.join(pdir, f"{i:04d}.txt"), p)

    ingest_io.write_json(
        os.path.join(base, "docmeta.json"),
        {
            "doc_id": bundle.doc_id,
            "routed": bundle.routed,
            "language": bundle.language,
            "page_offsets": bundle.page_offsets,
            "meta": bundle.meta,
        },
    )

    if cfg.keep_jsonl:
        ingest_io.write_text(os.path.join(base, "record.jsonl"), f"{asdict(bundle)}\n")

    return {"doc_id": doc_id, "out": base, "routed": routed, "language": language or "unknown", "token_count": token_count}
