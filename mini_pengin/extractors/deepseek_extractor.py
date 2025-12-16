from typing import List, Optional
from PIL import Image
import os
import fitz, torch
from transformers import AutoTokenizer, AutoModel

# =================== Hardening (CPU-only, macOS/Python 3.13) ===================
# Never expose a CUDA device; prefer simple, predictable CPU code paths.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Make torch report no CUDA
try:
    torch.cuda.is_available = lambda: False  # type: ignore[attr-defined]
except Exception:
    pass

# Patch autocast everywhere to CPU
try:
    from torch.amp.autocast_mode import autocast as _orig_autocast
    import torch.amp.autocast_mode as _am

    def _patched_autocast(*args, **kwargs):
        kwargs["device_type"] = "cpu"
        return _orig_autocast(**kwargs)

    _am.autocast = _patched_autocast  # type: ignore[assignment]
    if hasattr(torch, "autocast"):
        torch.autocast = _patched_autocast  # type: ignore[assignment]

    # torch.cuda.amp.autocast → no-op CPU ctx
    if hasattr(torch, "cuda"):
        class _CPUAutocastCtx:
            def __enter__(self): return self
            def __exit__(self, *a): return False
        torch.cuda.amp = type("amp", (), {"autocast": lambda *a, **k: _CPUAutocastCtx()})  # type: ignore[attr-defined]
except Exception:
    pass

# Tell transformers there is no CUDA
try:
    from transformers.utils import import_utils as _tf_imp
    _tf_imp.is_torch_cuda_available = lambda: False  # type: ignore[assignment]
except Exception:
    pass

# Provide safe fallbacks for attention symbols (older/newer transformers)
try:
    from transformers.models.llama import modeling_llama as _llama_mod
    import torch.nn as nn
    _Base = getattr(_llama_mod, "LlamaAttention", None)
    if _Base is None:
        class _Base(nn.Module):  # minimal placeholder (won't be executed)
            def __init__(self, *a, **k): super().__init__()
            def forward(self, *a, **k): raise RuntimeError("Flash/SDPA attention unavailable.")
    if not hasattr(_llama_mod, "LlamaFlashAttention2"):
        _llama_mod.LlamaFlashAttention2 = _Base  # type: ignore[attr-defined]
    if not hasattr(_llama_mod, "LlamaSdpaAttention"):
        _llama_mod.LlamaSdpaAttention = _Base  # type: ignore[attr-defined]
except Exception:
    pass

# Intercept any .to("cuda") / .to(torch.device("cuda")) calls at runtime
try:
    _orig_module_to = torch.nn.Module.to
    def _safe_to(self, *args, **kwargs):
        # normalize device param from args/kwargs
        device = None
        if args:
            device = args[0]
        elif "device" in kwargs:
            device = kwargs["device"]
        # Map any CUDA device to CPU
        if isinstance(device, str) and device.startswith("cuda"):
            device = "cpu"
        elif isinstance(device, torch.device) and device.type == "cuda":
            device = torch.device("cpu")
        # rebuild call
        if args:
            args = (device,) + tuple(args[1:])
            kwargs = {}
        else:
            kwargs["device"] = device
        return _orig_module_to(self, *args, **kwargs)
    torch.nn.Module.to = _safe_to  # type: ignore[assignment]
except Exception:
    pass
# ===============================================================================

_MODEL = None
_TOK = None
_DEV = None
_NAME = "deepseek-ai/DeepSeek-OCR"
_REVISION: Optional[str] = None  # set to a specific commit/tag to pin remote code

def _lazy():
    """Lazy-load tokenizer/model on CPU only (stable on macOS)."""
    global _MODEL, _TOK, _DEV
    if _MODEL is not None:
        return

    _DEV = "cpu"  # ← force CPU (MPS can be slow/flaky for this model)

    _TOK = AutoTokenizer.from_pretrained(_NAME, trust_remote_code=True, revision=_REVISION)
    _MODEL = AutoModel.from_pretrained(
        _NAME,
        trust_remote_code=True,
        use_safetensors=True,
        revision=_REVISION,
    ).eval()

    _MODEL = _MODEL.to(torch.float32)  # stay on CPU

def _render(pdf: str, dpi: int = 300) -> List[Image.Image]:
    """Render PDF pages to PIL images using PyMuPDF (no Poppler needed)."""
    images: List[Image.Image] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)
            del pix
    return images

def _tesseract_fallback(images: List[Image.Image], lang: Optional[str] = None) -> List[str]:
    """Fallback OCR via Tesseract if DeepSeek fails."""
    try:
        import pytesseract
    except Exception:
        # No pytesseract available → return empty strings (pipeline will still continue)
        return ["" for _ in images]
    out = []
    for im in images:
        try:
            out.append(pytesseract.image_to_string(im, lang=lang) if lang else pytesseract.image_to_string(im))
        except Exception:
            out.append("")
    return out

def ocr_pages_deepseek(
    pdf: str,
    dpi: int = 300,
    prompt_mode: str = "markdown",  # "markdown" | "plain"
    max_pages: Optional[int] = None,
) -> List[str]:
    """
    Returns per-page OCR text using DeepSeek-OCR via Transformers.
    - markdown: strong prompt for GitHub pipe-table syntax (parseable later)
    - plain   : free OCR text
    If DeepSeek fails for any reason, falls back to Tesseract OCR.
    """
    images = _render(pdf, dpi=dpi)
    if max_pages is not None:
        images = images[:max_pages]

    # Strong Markdown prompt baked in for --deepseek-prompt markdown
    if prompt_mode == "markdown":
        prompt = (
            "<image>\n"
            "Convert this page to clean Markdown. "
            "Use GitHub pipe table syntax (| and ---) for ALL tables. "
            "No images, no extra commentary."
        )
    else:
        prompt = "<image>\nFree OCR."

    # Try DeepSeek on CPU
    try:
        _lazy()
        out: List[str] = []
        import tempfile
        with tempfile.TemporaryDirectory() as td, torch.no_grad():
            for i, im in enumerate(images):
                fp = os.path.join(td, f"p{i}.jpg")
                im.save(fp, "JPEG", quality=95)

                # DeepSeek-OCR exposes .infer() via trust_remote_code
                res = _MODEL.infer(
                    _TOK,
                    prompt=prompt,
                    image_file=fp,
                    output_path=td,
                    base_size=1024,
                    image_size=640,
                    crop_mode=True,
                    save_results=False,
                    test_compress=False,
                )

                text = None
                if isinstance(res, dict):
                    text = res.get("text") or res.get("markdown") or res.get("output")
                elif isinstance(res, str):
                    text = res

                out.append((text or "").strip())
        return out

    except KeyboardInterrupt:
        raise
    except Exception:
        # Any DeepSeek failure → fallback OCR (local, CPU)
        return _tesseract_fallback(images)
