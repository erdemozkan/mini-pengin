from __future__ import annotations
from typing import Dict, List, Optional
import os
import pandas as pd

from .tables_utils import clean_df, score_table

def extract_tables_docling(pdf_path: str, out_dir: str) -> Dict:
    """Docling-first extractor:
    1) Run Docling with table structure ON (if pipeline options are available).
    2) Export table objects from the structured graph.
    3) Fallback: parse <table> nodes from full HTML export.
    All outputs are cleaned and scored before writing CSVs.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Build converter (version-agnostic options)
    from docling.document_converter import DocumentConverter
    opts = None
    try:
        from docling.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
        opts = PdfPipelineOptions(
            do_table_structure=True,
            table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE)
        )
    except Exception:
        opts = None

    conv = DocumentConverter(pipeline_options=opts) if opts else DocumentConverter()
    res = conv.convert(pdf_path)
    doc = res.document

    items: List[Dict] = []
    best: List[tuple[float, str]] = []

    # 1) Prefer structured table objects if present
    for i, tbl in enumerate(getattr(doc, "tables", []) or [], 1):
        try:
            raw_df: pd.DataFrame = tbl.export_to_dataframe()
        except Exception:
            continue
        df = clean_df(raw_df)
        if df is None:
            continue
        stem = os.path.join(out_dir, f"table_{i:02d}")
        csv_path = stem + ".csv"
        df.to_csv(csv_path, index=False)
        # save HTML snippet if available
        html_path = None
        try:
            html = tbl.export_to_html(doc=doc)
            html_path = stem + ".html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass
        items.append({"page": getattr(tbl, "page", None), "path_html": html_path, "path_csv": csv_path})
        best.append((score_table(df), csv_path))

    # 2) Fallback: parse <table> nodes from full HTML export (version-agnostic)
    if not items:
        to_html = getattr(doc, "export_to_html", None) or getattr(doc, "export_html", None)
        html_all = to_html() if callable(to_html) else ""
        if html_all:
            try:
                from bs4 import BeautifulSoup  # pip install beautifulsoup4
                soup = BeautifulSoup(html_all, "lxml")
                for k, node in enumerate(soup.find_all("table"), 1):
                    try:
                        dfs = pd.read_html(str(node))
                    except Exception:
                        dfs = []
                    if not dfs:
                        continue
                    df = clean_df(dfs[0])
                    if df is None:
                        continue
                    stem = os.path.join(out_dir, f"table_html_{k:02d}")
                    csv_path = stem + ".csv"
                    df.to_csv(csv_path, index=False)
                    with open(stem + ".html", "w", encoding="utf-8") as f:
                        f.write(str(node))
                    items.append({"page": None, "path_html": stem + ".html", "path_csv": csv_path})
                    best.append((score_table(df), csv_path))
            except Exception:
                pass

    return {"engine": "docling", "count": len(items), "items": items}
