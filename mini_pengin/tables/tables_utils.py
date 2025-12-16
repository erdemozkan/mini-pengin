import pandas as pd
import re

def clean_df(df: pd.DataFrame, min_rows: int = 2, min_cols: int = 2) -> pd.DataFrame | None:
    # 1) strip whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # 2) drop all-empty rows/cols  (FinePDFs does this)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.shape[0] < min_rows or df.shape[1] < min_cols:
        return None

    # 3) promote a header row when first row looks like headers
    def looks_like_header(row: pd.Series) -> bool:
        txt = " ".join([str(x) for x in row.values if isinstance(x, str)])
        caps = sum(w.istitle() or w.isupper() for w in txt.split())
        return caps >= max(1, len(txt.split()) // 3)

    if looks_like_header(df.iloc[0]):
        df.columns = [str(x) if pd.notna(x) else "" for x in df.iloc[0]]
        df = df.iloc[1:].reset_index(drop=True)

    # 4) normalize header names
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    # 5) normalize numeric columns (comma→dot) where safe
    for c in df.columns:
        if df[c].dropna().astype(str).str.fullmatch(r"[\d\.,%-]+").mean() > 0.8:
            df[c] = df[c].astype(str).str.replace(",", ".", regex=False)

    # 6) final empty drops
    df = df.dropna(how="all").dropna(axis=1, how="all")
    return df if df.shape[0] >= min_rows and df.shape[1] >= min_cols else None

def score_table(df: pd.DataFrame) -> float:
    # simple quality score: more rows/cols + fewer empties + header presence
    if df is None: return 0.0
    r, c = df.shape
    empties = df.isna().mean().mean()
    header_bonus = 0.2 if all(isinstance(x, str) and x for x in df.columns) else 0.0
    return (r * c) / (1 + 10 * empties) * (1 + header_bonus)
