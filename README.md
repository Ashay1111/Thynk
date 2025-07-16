# Thynk  
**Interactive knowledge base**  

---

## Overview

**Thynk** is a modular Retrieval-Augmented Generation (RAG) system built using LangChain, Gemini, and FAISS. It enables grounded, source-backed question answering over user-uploaded PDFs — with no hallucinations, no bluffing, and full transparency.

Thynk is designed for use in research, legal, educational, and any high-integrity domain where reliable answers matter more than eloquent guesses.

---

## Demo
Visit: https://youtu.be/37_5XXa4XI4
---

## Features

- Upload custom documents (PDFs)
- Index with configurable chunking (size and overlap)
- Query using Gemini with optional query expansion
- See expanded queries and retrieved context
- Strictly answers based on source content
- Modular backend split into indexing, retrieval, generation
- Clean web interface built with FastAPI and vanilla HTML/JS

---

## Tech Stack

- Python 3.12
- LangChain
- Gemini (via `langchain_google_genai`)
- FAISS
- FastAPI
- PyMuPDF (for PDF parsing)
- HTML / JS frontend

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Ashay1111/Thynk.git
cd Thynk
````

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your environment

Create a `.env` file in the root directory:

```bash
touch .env
```

Add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

### 5. Run the app

```bash
uvicorn scripts.app:app --reload
```

Visit in browser:
[http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
Thynk/
├── scripts/
│   ├── uploads/              # Folder to store uploaded PDFs
│   ├── .env                  # API key (ignored by Git)
│   ├── app.py                # FastAPI backend + endpoints
│   ├── indexing.py           # Loads, chunks, and embeds documents
│   ├── retrieval.py          # FAISS retrieval logic
│   ├── generation.py         # Answer generation via Gemini
│   ├── query_expansion.py    # Expands queries using LLM
│   ├── config.py             # Configuration and API key loading
│   ├── ui_interface.html     # Frontend interface
│   ├── main.py
│   └── __init__.py
├── sample_research_papers
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Usage Philosophy

Thynk prioritizes **grounded responses** over speculative completions. If the source doesn’t contain the answer, it won't fabricate one. This system is particularly suited for domains where incorrect answers are more dangerous than no answers.

---

## Future Directions

* Chunk-level re-ranking using Gemini
* Multi-query refinement chains
* Support for non-PDF sources (Markdown, HTML, JSONL)
* Authenticated multi-user mode with persistent upload history

---
