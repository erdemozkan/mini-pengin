import os
import pandas as pd

__all__ = ["extract_tables_from_markdown_pages", "_extract_md_tables"]

def _extract_md_tables(md: str):
    """
    Detect GitHub-style pipe tables in Markdown and return each table as a Markdown string.
    Heuristic:
      line i starts with '|' AND line i+1 is a delimiter of pipes/dashes/colons/spaces,
      followed by one or more lines starting with '|'.
    """
    tables = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines):
            delim = lines[i + 1].strip()
            if delim and set(delim) <= set("|:- "):
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    j += 1
                tables.append("\n".join(lines[i:j]))
                i = j
                continue
        i += 1
    return tables

def extract_tables_from_markdown_pages(page_markdowns, out_dir: str):
    """
    Parse Markdown pipe tables from OCR (DeepSeek) page outputs.
    Writes page-scoped .md and .csv files under out_dir.
    Returns {"engine": "markdown", "count": N, "items": [...]}
    """
    os.makedirs(out_dir, exist_ok=True)
    items = []
    count = 0

    # Optional MD→HTML converter to help pandas.read_html
    try:
        import markdown as mdlib  # type: ignore
    except Exception:
        mdlib = None

    for i, md in enumerate(page_markdowns, 1):
        tables = _extract_md_tables(md)
        for k, tmd in enumerate(tables, 1):
            base = os.path.join(out_dir, f"page_{i:04d}_table_{k:02d}")
            md_path = base + ".md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(tmd)

            html = mdlib.markdown(tmd) if mdlib is not None else None

            csv_path = None
            try:
                dfs = pd.read_html(html if html is not None else tmd)
                if dfs:
                    csv_path = base + ".csv"
                    dfs[0].to_csv(csv_path, index=False)
            except Exception:
                pass

            items.append({"page": i, "path_md": md_path, "path_html": None, "path_csv": csv_path})
            count += 1

    return {"engine": "markdown", "count": count, "items": items}
