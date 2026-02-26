# Document Metadata Extraction System

An AI-powered system that extracts structured metadata from rental/lease agreement documents (`.docx` and `.png` files) using Large Language Models (Google Gemini) with few-shot prompting.

---

## Solution Approach

### Architecture

```
Document (.docx / .png)
    │
    ▼
┌──────────────────────────┐
│  1. Text Extraction      │  python-docx (DOCX) / Tesseract OCR + OpenCV (images)
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  2. Prompt Construction  │  Few-shot prompt with 5 examples + chain-of-thought
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  3. LLM Inference        │  Google Gemini API (multi-model rotation + retries)
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  4. Post-Processing      │  Title stripping, date normalization, value cleaning
└──────────────────────────┘
    │
    ▼
  Structured JSON / CSV Output
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

**API Endpoints:**
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API status |
| GET | `/health` | Health check |
| POST | `/extract` | Upload file → extract metadata |

---

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

## Dependencies

| Package | Purpose |
|---|---|
| python-docx | Extract text from .docx files |
| pytesseract | OCR engine interface |
| Pillow | Image loading and basic processing |
| opencv-python | Advanced image preprocessing for OCR |
| numpy | Array operations for image processing |
| pandas | Data manipulation and CSV I/O |
| google-generativeai | Google Gemini API client |
| python-dotenv | Environment variable management |
| fastapi | REST API framework |
| uvicorn | ASGI server |
| python-multipart | File upload support for FastAPI |

---

## Deployment on Render

The API is deployed as a Docker-based web service on [Render](https://render.com).

### Live API URL

```
https://meta-data-extraction-from-documents.onrender.com
```

### How to Deploy (Step-by-Step)

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - metadata extraction system"
   git remote add origin https://github.com/<your-username>/metadata-extraction.git
   git push -u origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Select the `metadata-extraction` repo

3. **Configure the service**
   - **Name**: `metadata-extractor-api`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: Free (or Starter for better performance)

4. **Set Environment Variables**
   - Go to **Environment** tab
   - Add:
     - `GEMINI_API_KEY` = your Google Gemini API key
     - `GEMINI_API_KEY_2` = (optional) second API key for rotation

5. **Deploy**
   - Click **Create Web Service**
   - Render will build the Docker image and deploy automatically
   - Wait for deployment to show **Live** status

### Using the Deployed API

**Health Check:**
```bash
curl https://meta-data-extraction-from-documents.onrender.com/health
```

**Extract Metadata:**
```bash
curl -X POST "https://meta-data-extraction-from-documents.onrender.com/extract" \
  -F "file=@rental-agreement.docx"
```

**Interactive API Docs (Swagger):**
```
https://meta-data-extraction-from-documents.onrender.com/docs
```

> **Note**: Free tier instances spin down after inactivity. The first request after idle may take ~30-60 seconds.