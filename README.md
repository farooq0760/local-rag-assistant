# 🔒 Local RAG — Private Document Assistant

> 100% local. No cloud. No API keys. Your documents never leave your machine.

---

## ⏱️ Setup (under 1 hour)

### STEP 1 — Install Ollama (5 min)

1. Download from **https://ollama.com/download** → install for Windows
2. Open a terminal and pull the models:

```powershell
# Reasoning chat model (~4.7 GB)
ollama pull deepseek-r1:7b

# Local embedding model (~274 MB)
ollama pull nomic-embed-text
```

> Ollama runs silently in the background after install. No configuration needed.

---

### STEP 2 — Set Up Python Environment (5 min)

```powershell
# Navigate to this project
cd C:\Users\faroo\.gemini\antigravity\scratch\local-rag

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### STEP 3 — Configure (1 min)

```powershell
# Copy the example config
copy .env.example .env
```

Edit `.env` if needed (defaults work out of the box).

---

### STEP 4 — Add Your Documents (2 min)

Drop your files into the **`docs/`** folder:

| Format | Extension |
|--------|-----------|
| PDF | `.pdf` |
| Word | `.docx` |
| Excel | `.xlsx`, `.xls` |
| Text | `.txt`, `.md` |

Subfolders are supported — all files are scanned recursively.

---

### STEP 5 — Ingest Documents (5–15 min depending on size)

```powershell
python ingest.py
```

This embeds all your documents locally and stores them in `chroma_db/`.  
Run this again whenever you add or update documents.

---

### STEP 6 — Start Chatting! 🎉

```powershell
streamlit run app.py
```

Opens in your browser at **http://localhost:8501**

---

## 🗂️ Project Structure

```
local-rag/
├── docs/           ← Put your documents here
├── chroma_db/      ← Auto-created: local vector database
├── .env            ← Your local config (never commit this)
├── requirements.txt
├── ingest.py       ← Run to index your documents
└── app.py          ← Run to start the chat UI
```

---

## 🔒 Security Checklist

- [x] LLM runs locally via Ollama (no OpenAI/cloud API calls)
- [x] Embeddings generated locally with `nomic-embed-text`
- [x] Vector DB stored locally in `chroma_db/` folder
- [x] UI runs on `localhost` only (not exposed to network)
- [ ] **Enable BitLocker** on this drive (Windows Settings → Privacy & Security → Device Encryption)
- [ ] Add `docs/`, `chroma_db/`, `.env` to `.gitignore` if using git
- [ ] Keep Ollama's network access as `localhost` only (default behavior)

---

## 💡 Tips

- **Re-ingest after adding documents**: Run `python ingest.py` again
- **Toggle reasoning**: Use the sidebar in the UI to show/hide model thinking
- **Want a better model?** Try `ollama pull llama3.1:8b` and update `.env`
- **Slow responses?** A GPU (NVIDIA) speeds this up dramatically

---

## 🧠 How It Works

```
Your Question
     │
     ▼
[Embed question locally]  ←── nomic-embed-text
     │
     ▼
[Search chroma_db for similar chunks]  ←── ChromaDB
     │
     ▼
[Top 5 relevant document chunks]
     │
     ▼
[Feed to deepseek-r1:7b with prompt]  ←── Ollama (local)
     │
     ▼
Answer + Reasoning + Source citations
```
