# RAG System

Sistema de **Retrieval-Augmented Generation (RAG)** que permite conversar com seus documentos utilizando uma stack local.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| Orquestração RAG | LangChain |
| Banco Vetorial | Qdrant |
| LLM | Ollama (llama3.2) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Parsing de Documentos | pypdf, python-docx |

---

## Funcionalidades

- Upload de arquivos **PDF, DOCX, TXT e Markdown**
- Indexação de texto diretamente pela interface
- Chat com seus documentos usando um LLM local
- **Slider de top-k** ajustável por consulta
- **Gerenciamento de documentos:** listar e deletar documentos indexados
- Atualização automática da lista após cada upload
- Funciona localmente com Ollama e Sentence Transformers


---

## Pré-requisitos

- **Python** 3.11+
- **Node.js** 18+
- **Docker** (para o Qdrant)
- **Ollama** com o modelo llama3.2

---

## Como Rodar

### 1. Clone o repositório

```bash
git clone https://github.com/RafaelShort/rag-chatbot.git
cd rag-chatbot
```

### 2. Inicie o Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 3. Baixe o modelo Ollama

```bash
ollama pull llama3.2
```

### 4. Configure o backend

```bash
cp .env.example backend/.env
```

### 5. Instale e rode o backend

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 6. Instale e rode o frontend

```bash
cd frontend
npm install
npm run dev
```
