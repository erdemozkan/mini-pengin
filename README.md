# mini-pengin

A production-grade, local-first PDF ingestion pipeline optimized for macOS silicon. Designed to convert 1–2 page documents into clean, structured data for RAG/LLM applications.

**Linux Usage**: Fully compatible with Linux (x86/ARM). Defaults to CPU execution for consistency. To enable CUDA/GPU acceleration, remove the macOS-hardening overrides in `mini_pengin/extractors/deepseek_extractor.py`.

## Architecture

This pipeline implements a "router-first" approach to balance speed and accuracy:

1.  **ScanGate Router**: Analyzes text density to intelligently route documents between native extraction and OCR.
2.  **Hybrid Extraction**:
    *   **Native**: High-fidelity extraction using `PyMuPDF` for digital-born documents.
    *   **OCR**: **DeepSeek-OCR** (via `transformers`) running locally. Explicitly hardened for macOS to run purely on CPU/RAM, bypassing MPS/CUDA stability issues while maintaining high accuracy.
3.  **Table Intelligence**: Cascading extraction strategy:
    *   **Docling**: Primary engine for complex table structures.
    *   **DeepSeek-Markdown**: Parses tables directly from VLM markdown output.
    *   **Camelot**: Fallback for traditional lattice/stream structures.
4.  **Post-Processing Fabric**:
    *   `BoilerSkim`: Filters out irrelevant cover pages and legal disclaimers.
    *   `PageTagWiper`: Strips artifacts like headers, footers, and page numbers.
    *   `ParaWeld`: Reconstructs semantic paragraphs from broken lines and soft line breaks.
    *   `MarklistNormalizer`: Standardizes list formats.

## Tech Stack

*   **Core**: Python 3.9+
*   **OCR**: DeepSeek-OCR (HuggingFace Transformers)
*   **Tables**: Docling, Camelot
*   **Processing**: PyMuPDF, Pandas, Torch (CPU mode)
*   **Output**: JSONL, Markdown, Clean Text

## CLI Usage

Run the pipeline via the command line:

```bash
python -m mini_pengin --input <INPUT_DIR> --out <OUTPUT_DIR> [OPTIONS]
```

### Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--input` | Directory containing PDFs to process (required). | - |
| `--out` | Output directory for results (required). | - |
| `--ocr` | OCR engine: `auto`, `deepseek`, `tesseract`, or `off`. | `auto` |
| `--tables` | Table engine: `auto`, `docling`, `camelot`, or `off`. | `auto` |
| `--workers` | Number of parallel worker threads. | `2` |
| `--save-pages`| Save individual page text files. | `False` |
| `--keep-jsonl`| Save a `record.jsonl` with full metadata. | `False` |

**Example**:
```bash
# Process PDFs using 4 workers, saving page text and using Docling for tables
python -m mini_pengin --input ./in --out ./out --workers 4 --save-pages --tables docling
```
