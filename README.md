@'
# RAG System

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you chat with your documents using a fully local setup — no data leaves your machine.

Built with FastAPI, React, Qdrant and Ollama.

---

## Features

- Upload **PDF, DOCX, TXT and Markdown** files
- Index raw text directly from the UI
- Chat with your documents using a local LLM
- Adjustable **top-k retrieval slider** per query
- **Document management** — list and delete indexed documents
- Auto-refresh document list after each upload
- 100% local — works with Ollama + Sentence Transformers

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| RAG Orchestration | LangChain |
| Vector Store | Qdrant |
| LLM | Ollama (llama3.2) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Document Parsing | pypdf, python-docx |

---


---

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **Docker** (for Qdrant)
- **Ollama** with llama3.2 model

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rag-system.git
cd rag-system


