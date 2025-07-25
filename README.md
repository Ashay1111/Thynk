# Thynk  
**Interactive knowledge base**  

---

## Overview

**Thynk** is a modular Retrieval-Augmented Generation (RAG) system built using LangChain, Gemini, and FAISS. It enables grounded, source-backed question answering over user-uploaded PDFs — with no hallucinations, no bluffing, and full transparency.

Thynk is designed for use in research, legal, educational, and any high-integrity domain where reliable answers matter more than eloquent guesses.


## Features

- Upload custom documents (PDFs)
- Index with configurable chunking (size and overlap)
- Query using Gemini with optional query expansion
- See expanded queries and retrieved context
- Strictly answers based on source content
- Modular backend split into indexing, retrieval, generation
- Clean web interface built with FastAPI and vanilla HTML/JS

---

## ⚠️ Limitations

### . Railway Hosting (Free Tier)

This project is currently hosted on [Railway](https://railway.app/) using the free tier. Please note:

- The backend sleeps after **15 minutes** of inactivity.
- On first request after sleep, the server can take **up to 60 seconds** to wake up.
- You might see delayed responses or errors like `500` or `404` if the server hasn't fully started. Simply **refresh after a few seconds**.


## If you're a recruiter or interested in using or extending this project, feel free to reach out:

-  **Email**: `ashayjpatel@gmail.com`
- [LinkedIn](https://linkedin.com/in/ashayjpatel)
  
---
### **Live Demo** : [Visit the Website](https://thynk-production.up.railway.app/)

### **Watch the Walkthrough**: [YouTube Demo](https://youtu.be/37_5XXa4XI4)
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

## Project Structure

```
Thynk/
├── frontend/                      # User interface (HTML, CSS, JS)
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── sample_research_papers/       # Example documents for testing
│   └── ...                       # (PDFs or other supported files)
│
├── scripts/                      # Backend logic for RAG pipeline
│   ├── uploads/              # Folder to store uploaded PDFs
│   ├── .env                  # API key (ignored by Git)
│   ├── cli.py                # FastAPI backend + endpoints
│   ├── indexing.py           # Loads, chunks, and embeds documents
│   ├── retrieval.py          # FAISS retrieval logic
│   ├── generation.py         # Answer generation via Gemini
│   ├── query_expansion.py    # Expands queries using LLM
│   ├── config.py             # Configuration and API key loading
│   ├── server.py
│   ├── core.py
│   └── __init__.py
│
├── .gitignore
├── Procfile                      # Railway deployment config
├── README.md
├── requirements.txt              # Python dependencies

```

---

## Usage Philosophy

Thynk prioritizes **grounded responses** over speculative completions. If the source doesn’t contain the answer, it won't fabricate one. This system is particularly suited for domains where incorrect answers are more dangerous than no answers.

---

## Future Directions

* Pinecone integration for scalable, production-grade vector storage
* Neural re-ranking of retrieved chunks using Gemini for smarter retrieval
* Authenticated multi-user mode with persistent upload history
* Multi-query refinement chains for enhanced answer quality
* Support for non-PDF sources (Markdown, HTML, JSONL)
* Interactive React frontend to visualize retrieval + re-ranking flow

---
