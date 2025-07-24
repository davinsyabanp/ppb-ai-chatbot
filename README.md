# RAG Chatbot AI (PPB UIN Jakarta)

A Retrieval-Augmented Generation (RAG) chatbot that answers questions based on local documents, accessible via a web admin dashboard and chat interface. Supports Google Gemini, local LLMs via Ollama, and advanced evaluation with RAGAS or custom LLM metrics.

---

## Features

- 🤖 **RAG-powered responses** based on local document knowledge base
- 🧠 **Google Gemini** and **Ollama (local LLMs)** for text generation
- 🔍 **Local embeddings** using Nomic Atlas
- 📚 **FAISS vector store** for efficient document retrieval
- 📄 **Multi-format support** (PDF, TXT, CSV documents)
- 📊 **CSV processing** with row-by-row conversion for structured data
- 🛡️ **Admin dashboard** for file upload, chunk preview, embedding, and vector DB management
- 🧩 **Chunk preview** before embedding
- 🗑️ **Vector DB management** (delete, re-embed)
- 📈 **Evaluation scripts**: RAGAS (OpenAI), Gemini, and Ollama (local)
- 🛡️ **Langsmith monitoring** and tracing support
- 🎨 **Modern UI** with Tailwind CSS

---

## Prerequisites

- **Python 3.8+**
- **Node.js & npm** (for Tailwind CSS build)
- **Nomic API key** (for embeddings)
- **Google API key** (for Gemini, if used)
- **Ollama** (for local LLMs, e.g., llama3, deepseek, mistral, etc.)
- **openpyxl** (for Excel evaluation output)
- (Optional) **OpenAI API key** (for RAGAS evaluation)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Chatbot\ AI\ All\ Using\ API\ Ver\ 1.1.0
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install openpyxl
   ```

3. **Install Node.js dependencies (for Tailwind CSS):**
   ```bash
   npm install
   ```

4. **Configure environment variables:**
   ```bash
   cp env.example .env
   ```
   Edit `.env` with your credentials (see `env.example` for all options).

---

## Project Structure

```
Chatbot AI All Using API Ver 1.1.0/
├── app/
│   ├── __init__.py
│   ├── core.py            # RAG chain logic
│   ├── models.py          # LLM and embedding model initialization
│   └── vector_store.py    # FAISS vector store operations
├── documents/             # Source documents folder (PDF, CSV, etc.)
├── vector_db/             # FAISS index and vector store
├── main.py                # Flask web server (admin dashboard, API)
├── ingest.py              # Document processing script
├── evaluation.py          # RAGAS/OpenAI evaluation script
├── gemini_evaluation.py   # Gemini-based evaluation script
├── ollama_evaluation.py   # Ollama-based (local LLM) evaluation script
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
├── package.json           # Node.js scripts and dependencies
├── tailwind.config.js     # Tailwind CSS config
├── src/input.css          # Tailwind CSS input
├── static/css/output.css  # Tailwind CSS output (auto-generated)
├── static/images/         # UI images (e.g., logo)
├── templates/             # HTML templates (admin, chat, login)
├── build_css.py           # Python script to build Tailwind CSS
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

---

## Usage

### 1. Add Documents
Place your source documents (PDF, TXT, CSV) in the `documents/` folder.

### 2. Build Tailwind CSS (for UI)
You can use either npm or Python:
- **With npm:**
  ```bash
  npm run build-prod
  ```
- **With Python:**
  ```bash
  python build_css.py
  ```
This generates `static/css/output.css` for the web UI.

### 3. Create Vector Store
```bash
python ingest.py
```
This will:
- Load documents from the `documents/` folder
- Process CSV files row by row
- Create embeddings using Nomic
- Save the FAISS vector store to `vector_db/`

### 4. Start the Flask Server
```bash
python main.py
```
The server will start on `http://localhost:5000`

---

## Admin Dashboard

- **URL:** `/admin`
- **Features:**
  - Upload documents (PDF, TXT, CSV)
  - Preview chunking before embedding
  - Embed all files to vector DB
  - Delete individual files (removes from DB and disk)
  - Delete all vector DB contents (enables re-embedding)
  - View file status and embedding progress

---

## Evaluation & Monitoring

### **A. RAGAS Evaluation (OpenAI, for benchmarking)**
```bash
python evaluation.py
```
- Evaluates RAG pipeline using RAGAS metrics (faithfulness, answer relevancy, context precision, context recall)
- Requires `OPENAI_API_KEY` in `.env`

### **B. Gemini-based Evaluation (Indonesian prompts, LLM-as-a-judge)**
```bash
python gemini_evaluation.py
```
- Uses Google Gemini to evaluate RAG answers with custom Indonesian prompts
- Results saved as CSV and Excel

### **C. Ollama-based Evaluation (Local LLM, LLM-as-a-judge)**
```bash
python ollama_evaluation.py
```
- Uses a local LLM (default: `deepseek-r1:8b`, can be changed) via Ollama
- Interactive: choose to evaluate all or a sample of questions
- Results saved as CSV and Excel (multi-sheet, formatted)
- Progress updates every 10 questions

#### **Change Ollama Model**
Edit the `model_name` variable in `ollama_evaluation.py` (e.g., `deepseek-r1:8b`, `llama3.2:3b`, `mistral:7b`)

#### **Excel Output**
- Results are saved as `ollama_evaluation_results_YYYYMMDD_HHMMSS.xlsx` in the project root
- Includes summary, detailed results, and explanations

### D. RAGAS Evaluation with Vertex AI (Google Cloud LLM-as-a-judge)

See `env.example` for required GCP environment variables.

---

## Environment Variables

See `env.example` for all required and optional variables, including:
- `GOOGLE_API_KEY`
- `NOMIC_API_KEY`
- `JINA_API_KEY`
- `LANGCHAIN_*` (for Langsmith tracing)
- `OPENAI_API_KEY` 
- `GCP_PROJECT_ID`, `GCP_REGION` (for Vertex AI evaluation)

---

## Frontend Build (Tailwind CSS)

- **Input:** `src/input.css`
- **Output:** `static/css/output.css`
- **Config:** `tailwind.config.js`
- **Build:** `npm run build-prod` or `python build_css.py`

---

## Security & Best Practices

- **Never commit your `.env` file or secret keys**
- `.gitignore` is set up to ignore secrets, data, and generated files
- Use a separate environment for development and production
- Regularly update dependencies

---

## Troubleshooting

- **Ollama timeout or memory errors:**
  - Use a smaller model (e.g., `llama3.2:3b`)
  - Increase timeout in `ollama_evaluation.py` if needed
  - Ensure your machine has enough RAM/CPU
- **Vector store not found:**
  - Run `python ingest.py` to create the vector store
- **API key errors:**
  - Check your `.env` file for correct keys
- **Evaluation script errors:**
  - Ensure all dependencies are installed (`pip install -r requirements.txt openpyxl`)
  - Check for error messages in the terminal
- **Tailwind CSS build errors:**
  - Ensure Node.js and npm are installed
  - Run `npm install` before building CSS

---

## License

This project is licensed under the MIT License.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## About

This chatbot is designed for the Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta, with support for Indonesian language, local document retrieval, and advanced evaluation workflows for RAG systems.

--- 