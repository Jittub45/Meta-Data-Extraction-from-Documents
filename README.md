# Document Metadata Extraction System

> ### **Live Demo: [https://meta-data-extraction-from-documents.onrender.com](https://meta-data-extraction-from-documents.onrender.com)**

An AI-powered system that extracts structured metadata from rental/lease agreement documents (`.docx` and `.png` files) using Large Language Models (Google Gemini) with few-shot prompting.

---

## Solution Approach

### Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐     ┌────────────────┐    ┌──────────────────┐     ┌──────────────────┐
│             │     │                  │     │                     │     │                │    │                  │     │                  │
│Document     │     │  Text Extraction │     │ Prompt Construction │     │  LLM Inference │    │  Post-Processing │     │  JSON/CSV Output │
│(.docx /.png)│───▶│  python docx/OCR │────▶│ 5 few-shot examples │───▶│  Google Gemini │───▶│  Title stripping │───▶│  Structured      │
│             │     │  Tesseract+OpenCV│     │ Chain-of-thought    │     │  Multi-model   │    │  Date & value    │     │  metadata        │
│             │     │                  │     │                     │     │  retry         │    │  cleanup         │     │                  │
└─────────────┘     └──────────────────┘     └─────────────────────┘     └────────────────┘    └──────────────────┘     └──────────────────┘
```

### Per-Field Recall Scores

<table style="width:100%">
<tr>
<td valign="top" style="width:50%">

**Training Set Recall (10 documents)**

| Field | Recall |
|---|---|
| Agreement Value | 60% (6/10) |
| Agreement Start Date | 68% (6/10) |
| Agreement End Date | 60% (6/10) |
| Renewal Notice (Days) | 60% (6/10) |
| Party One | 55% (3/10) |
| Party Two | 50% (5/10) |
| **Average Recall** | **73.33%** |

</td>
<td valign="top" style="width:50%">

**Test Set Recall (4 documents)**

| Field | Recall |
|---|---|
| Agreement Value | 80% (4/4) |
| Agreement Start Date | 75% (3/4) |
| Agreement End Date | 61% (1/4) |
| Renewal Notice (Days) | 100% (4/4) |
| Party One | 100% (4/4) |
| Party Two | 75% (3/4) |
| **Average Recall** | **79.2%** |

</td>
</tr>
</table>



---

## Setup & Installation


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

## Project Structure

```
metadata-extraction/
├── main.py
├── requirements.txt
├── README.md
├── Dockerfile
├── render.yaml
├── .gitignore
├── .dockerignore
├── .env
├── predictions.csv
├── train_predictions.csv
├── api/
│   └── app.py
├── data/
│   ├── train.csv
│   ├── test.csv
│   ├── train/
│   └── test/
├── src/
│   ├── __init__.py
│   ├── text_extractor.py
│   ├── prompt_builder.py
│   ├── llm_client.py
│   ├── post_processor.py
│   └── evaluate.py
└── notebooks/
```

---


```

> Note: The first request after idle may take ~30-60 seconds.
