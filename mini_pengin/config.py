from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ForgeConfig:
    min_text_page_ratio: float = 0.55
    max_pages_probe: int = 12
    ocr_engine: str = "auto"            # auto|tesseract|deepseek|off
    ocr_lang: Optional[str] = None
    deepseek_prompt: str = "markdown"   # markdown|plain
    text_engine: str = "pymupdf"
    lang_detector: str = "auto"
    save_pages: bool = False
    keep_jsonl: bool = False
    workers: int = 2
    classify_kind: bool = False
    doc_kind_mode: str = "zero-shot"
    doc_kind_model: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    doc_kind_labels: List[str] = field(default_factory=lambda: [
        "invoice","receipt","resume","academic_paper","legal_contract","form","slides","report","other"
    ])
    doc_kind_hypothesis: str = "This document is {}."
    tables: str = "auto"                # auto|docling|off
