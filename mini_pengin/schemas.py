from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class PageInfo:
    index: int
    chars: int
    images: int

@dataclass
class DocProbe:
    num_pages: int
    pages: List[PageInfo]
    text_pages: int
    text_page_ratio: float

@dataclass
class DocBundle:
    doc_id: str
    text: str
    page_slices: List[str]
    page_offsets: List[int]
    routed: str
    language: Optional[str] = None
    meta: Dict = field(default_factory=dict)
