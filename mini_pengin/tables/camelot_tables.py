import os
from typing import Dict, List

from .tables_utils import clean_df, score_table

def extract_tables_camelot(pdf_path: str, out_dir: str) -> Dict:
    """Camelot extractor (lattice→stream). Cleans tables before writing CSVs."""
    try:
        import camelot  # brew install ghostscript; pip install "camelot-py[cv]" opencv-python-headless pandas lxml
    except Exception as e:
        return {"engine": "camelot", "error": f"camelot_not_available: {e}", "count": 0, "items": []}

    os.makedirs(out_dir, exist_ok=True)
    items: List[Dict] = []

    def _dump(tables, flavor: str):
        nonlocal items
        for idx, t in enumerate(tables, 1):
            df = clean_df(t.df)
            if df is None:
                continue
            stem = os.path.join(out_dir, f"camelot_{flavor}_{idx:02d}")
            csv = stem + ".csv"
            df.to_csv(csv, index=False)
            page = int(getattr(t, "page", 0) or 0)
            items.append({"page": page, "path_html": None, "path_csv": csv})

    # lattice first (ruled tables)
    try:
        tbls = camelot.read_pdf(pdf_path, flavor="lattice", pages="all")
        if len(tbls):
            _dump(tbls, "lattice")
    except Exception:
        pass

    # stream second (borderless)
    try:
        tbls = camelot.read_pdf(pdf_path, flavor="stream", pages="all")
        if len(tbls):
            _dump(tbls, "stream")
    except Exception:
        pass

    return {"engine": "camelot", "count": len(items), "items": items}
