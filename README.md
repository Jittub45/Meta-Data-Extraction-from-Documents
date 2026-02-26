# Document Metadata Extraction System

> ### **Live Demo: [https://meta-data-extraction-from-documents.onrender.com](https://meta-data-extraction-from-documents.onrender.com)**

An AI-powered system that extracts structured metadata from rental/lease agreement documents (`.docx` and `.png` files) using Large Language Models (Google Gemini) with few-shot prompting.

---

## Solution Approach

### Architecture

```
Document (.docx/.png) ──▶ Text Extraction ──▶ Prompt Construction ──▶ LLM Inference ──▶ Post-Processing ──▶ JSON/CSV Output
                          python-docx / OCR    5 few-shot examples     Google Gemini      Title stripping
                          Tesseract + OpenCV   Chain-of-thought        Multi-model retry  Date & value cleanup
```

### Key Design Decisions

1. **LLM-Based Extraction (Not Rule-Based)**: Uses Google Gemini with carefully crafted few-shot prompts instead of regex or static conditions. The LLM generalizes across varying document templates and formats.

2. **Advanced OCR Pipeline**: For `.png` files, uses OpenCV preprocessing (adaptive thresholding, denoising, resizing, sharpening) combined with multiple Tesseract PSM modes to maximize text extraction quality.

3. **Robust Post-Processing**: Strips honorific titles (Mr., Mrs., Prof., etc.) from party names, normalizes dates to DD.MM.YYYY format, and cleans currency values — all to match the expected ground truth format.

4. **Fault-Tolerant LLM Client**: Implements retry logic (up to 10 attempts), model rotation across 4 Gemini variants, API key rotation, robust JSON parsing with 6 fallback strategies, and metadata validation.

### Modules

| Module | Description |
|---|---|
| `src/text_extractor.py` | Extracts text from `.docx` (python-docx) and `.png` (Tesseract OCR + OpenCV) files |
| `src/prompt_builder.py` | Builds few-shot prompts with 5 diverse examples and detailed extraction rules |
| `src/llm_client.py` | Handles Gemini API calls with retry/rotation logic and robust JSON parsing |
| `src/post_processor.py` | Cleans and normalizes extracted values (titles, dates, numbers) |
| `src/evaluate.py` | Computes per-field Recall metric |
| `main.py` | Orchestrates the entire pipeline |
| `api/app.py` | FastAPI REST API wrapper |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed (for `.png` processing)
  - Windows: Install to `C:\Program Files\Tesseract-OCR\`
  - Linux: `sudo apt install tesseract-ocr`
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd metadata-extraction

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
# Optional: add a second key for rotation
echo "GEMINI_API_KEY_2=your_second_key_here" >> .env
```

---

## How to Run

### Option 1: Full Pipeline (Interactive)

```bash
python main.py
```

This will prompt you to choose:
1. **Validate on training data** — processes train/ documents and computes recall against train.csv
2. **Predict on test data** — processes test/ documents and saves predictions.csv
3. **Both** — runs validation then prediction

### Option 2: REST API

```bash
# Start the API server
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

Then upload a document:

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@path/to/document.docx"
```

**Response:**
```json
{
  "filename": "document.docx",
  "metadata": {
    "Agreement Value": "8000",
    "Agreement Start Date": "01.04.2011",
    "Agreement End Date": "31.03.2012",
    "Renewal Notice (Days)": "90",
    "Party One": "K. Parthasarathy",
    "Party Two": "Veerabrahmam Bathini"
  },
  "status": "success"
}
```
## Test Set Predictions

Predictions for the 4 files in the `test/` folder (saved in `predictions.csv`):

| File Name | Agreement Value | Start Date | End Date | Renewal Notice (Days) | Party One | Party Two |
|---|---|---|---|---|---|---|
| 24158401-Rental-Agreement | 12000 | 01.04.2008 | 31.03.2009 | 60 | Hanumaiah | Vishal Bhardwaj |
| 95980236-Rental-Agreement | 9000 | 01.04.2010 | 31.02.2011 | 30 | S.Sakunthala | V.V.Ravi Kian |
| 156155545-Rental-Agreement-Kns-Home | 12000 | 15.12.2012 | 15.11.2013 | 30 | V.K.NATARAJ | VYSHNAVI DAIRY SPECIALITIES Private Ltd |
| 228094620-Rental-Agreement | 15000 | 02.07.2013 | 31.05.2014 | 30 | KAPIL MEHROTRA | B.Kishore |

> **Note**: LLM outputs may vary slightly between runs. Run `python main.py` (option 2) to regenerate predictions.

---

## Per-Field Recall Scores

### Training Set Recall (10 documents)

| Field | Recall |
|---|---|
| Agreement Value | 60% (6/10) |
| Agreement Start Date | 60% (6/10) |
| Agreement End Date | 60% (6/10) |
| Renewal Notice (Days) | 60% (6/10) |
| Party One | 30% (3/10) |
| Party Two | 50% (5/10) |
| **Average Recall** | **53.33%** |

### Test Set Recall (4 documents)

| Field | Recall |
|---|---|
| Agreement Value | 100% (4/4) |
| Agreement Start Date | 75% (3/4) |
| Agreement End Date | 25% (1/4) |
| Renewal Notice (Days) | 100% (4/4) |
| Party One | 100% (4/4) |
| Party Two | 75% (3/4) |
| **Average Recall** | **79.2%** |

### Key Observations

- **High accuracy on structured DOCX files** — near-perfect extraction when text is clean
- **OCR challenges on PNG files** — two PNG files (54770958, 54945838) have swapped content in the image vs filename, causing mismatches
- **Date calculation edge cases** — LLM occasionally computes end dates differently (e.g., 31.02 vs 31.03)
- **Party name variations** — minor differences like `Q` vs `O`, commas vs periods from OCR artifacts

---

## Project Structure

```
metadata-extraction/
├── main.py                  # Main pipeline orchestrator
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── Dockerfile               # Docker config for Render deployment
├── render.yaml              # Render service configuration
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker ignore rules
├── .env                     # API keys (not committed)
├── predictions.csv          # Test set predictions (generated)
├── train_predictions.csv    # Training set predictions (generated)
├── api/
│   └── app.py               # FastAPI REST API
├── data/
│   ├── train.csv            # Training ground truth
│   ├── test.csv             # Test ground truth
│   ├── train/               # Training documents (.docx, .png)
│   └── test/                # Test documents (.docx, .png)
├── src/
│   ├── __init__.py
│   ├── text_extractor.py    # DOCX + OCR text extraction
│   ├── prompt_builder.py    # Few-shot prompt construction
│   ├── llm_client.py        # Gemini API client with retries
│   ├── post_processor.py    # Output cleaning & normalization
│   └── evaluate.py          # Recall metric computation
└── notebooks/               # Jupyter notebooks (exploration)
```

---


https://meta-data-extraction-from-documents.onrender.com
```

> **Note**: Free tier instances spin down after inactivity. The first request after idle may take ~30-60 seconds.