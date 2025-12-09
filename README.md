# RAG Chatbot AI (PPB UIN Jakarta)

A Retrieval-Augmented Generation (RAG) chatbot that answers questions based on local documents, accessible via a web admin dashboard and chat interface. Built with Flask, Google Gemini, Nomic Embeddings, and FAISS vector store.

---

## Features

- 🤖 **RAG-powered responses** based on local document knowledge base
- 🧠 **Google Gemini** for text generation
- 🔍 **Nomic Embedding** for text embedding
- 🏆 **Jina Reranker** for re-rank the retrieved documents
- 📚 **FAISS vector store** for efficient document retrieval
- 📄 **Multi-format support** (PDF, TXT, CSV documents)
- 📊 **CSV processing** with row-by-row conversion for structured data
- 🛡️ **Admin dashboard** for file upload, chunk preview, embedding, and vector DB management
- 🧩 **Chunk preview** before embedding
- 🗑️ **Vector DB management** (delete, re-embed)
- 🛡️ **Langsmith monitoring** and tracing support
- 🎨 **Modern UI** with Tailwind CSS and Bootstrap Icons
- 🔐 **Secure admin authentication** with login system
- 📱 **Responsive design** for mobile and desktop

---

## Prerequisites

- **Python 3.8+**
- **Node.js & npm** (for Tailwind CSS build)
- **Nomic API key** (for embeddings)
- **Google API key** (for text generation)
- **Jina API key** (for document reranking)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ppb-ai-chatbot
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
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

5. **Initialize the database and create admin user:**
   ```bash
   python main.py init-db
   ```

---

## Project Structure

```
ppb-ai-chatbot/
├── app/
│   ├── __init__.py
│   ├── core.py            # RAG chain logic and file processing
│   ├── models.py          # Database models and LLM initialization
│   └── vector_store.py    # FAISS vector store operations with Jina reranking
├── documents/             # Source documents folder (PDF, CSV, TXT)
├── vector_db/             # FAISS index and vector store
├── static/
│   ├── css/               # Tailwind CSS output
│   └── images/            # UI images (PPBOT_Logo.png)
├── templates/
│   ├── admin_dashboard.html  # Admin interface for file management
│   ├── admin_login.html      # Admin authentication page
│   └── chat.html             # User chat interface
├── main.py                # Flask web server with admin dashboard and API
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
├── package.json           # Node.js scripts and dependencies
├── tailwind.config.js     # Tailwind CSS configuration
├── src/input.css          # Tailwind CSS input
├── build_css.py           # Python script to build Tailwind CSS
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

---

## System Architecture

### 1. RAG Flow Diagram

Diagram berikut menunjukkan alur dasar sistem RAG:

```mermaid
graph LR
    A[User Query] --> B[Retriever]
    B --> C[Knowledge Base]
    C --> B
    B --> D[Generator]
    D --> E[Response]
    
    style A fill:#e1f5ff
    style E fill:#e1f5ff
    style B fill:#fff4e1
    style D fill:#fff4e1
    style C fill:#e8f5e9
```

### 2. Sistem RAG - Fase Indexing & Retrieval

Diagram berikut menunjukkan dua fase utama sistem RAG: Fase Indexing dan Fase Retrieval & Generation:

```mermaid
graph TB
    subgraph Indexing["Fase Indexing"]
        A1["Documents Directory<br/>/documents<br/>PDF, TXT, CSV"] --> A2["Document Loading<br/>PyMuPDFLoader, pandas<br/>ingest.py"]
        A2 --> A3["Text Splitting<br/>RecursiveCharacterTextSplitter<br/>ingest.py"]
        A3 --> A4["Text Embedding<br/>Nomic Atlas<br/>nomic-embed-text-v1.5<br/>ingest.py"]
        A4 --> A5["Vector Storage<br/>FAISS Vector Store<br/>/vector_db/<br/>ingest.py"]
    end
    
    subgraph Retrieval["Fase Retrieval & Generation"]
        B1["User Query<br/>Web Interface<br/>main.py"] --> B2["Hybrid Retrieval<br/>Semantic + Keyword Search<br/>hybrid_retrieve<br/>app/core.py"]
        B2 --> B3["FAISS Vector Store<br/>Similarity Search<br/>/vector_db/"]
        B3 --> B4["Document Reranking<br/>Jina AI Reranker<br/>jina-reranker-v2-base-multilingual<br/>app/vector_store.py"]
        B4 --> B5["Prompt Augmentation<br/>ChatPromptTemplate<br/>Context + Query<br/>app/core.py"]
        B5 --> B6["Answer Generation<br/>Google Gemini LLM<br/>gemini-2.0-flash<br/>app/models.py"]
        B6 --> B7["Response to User<br/>Web Interface<br/>main.py"]
    end
    
    A5 -.->|"Stored Vectors"| B3
    
    style Indexing fill:#e3f2fd
    style Retrieval fill:#f3e5f5
```

### 3. System Architecture - Web Application

Diagram berikut menunjukkan arsitektur lengkap aplikasi web dengan Flask:

```mermaid
graph TB
    subgraph Frontend["Frontend (Browser/Client Side)"]
        F1["Pengguna Umum Browser"] --> F2["chat.html<br/>Tailwind CSS + JavaScript"]
        F3["Administrator Browser"] --> F4["admin_dashboard.html<br/>Tailwind CSS + JavaScript"]
        F2 -->|"HTTP Request /chat"| Backend1
        F4 -->|"HTTP Request /admin"| Backend1
        Backend1 -->|"JSON Response"| F2
        Backend1 -->|"Dashboard Data"| F4
    end
    
    subgraph Backend["Backend (Aplikasi Flask Server-Side)"]
        Backend1["main.py<br/>Entry Point & Routing"] --> Backend2["app/core.py<br/>RAG Orchestration<br/>get_response()"]
        Backend2 --> Backend3["app/models.py<br/>SQLAlchemy Models<br/>AI Model Init"]
        Backend2 --> Backend4["app/vector_store.py<br/>Vector Operations<br/>create_vector_store()<br/>hybrid_retrieve()"]
        Backend1 -->|"Calls get_response"| Backend2
        Backend2 -->|"Uses Models"| Backend3
        Backend2 -->|"Calls retrieve"| Backend4
        Backend2 -->|"RAG Response"| Backend1
    end
    
    subgraph DataLayer["Data Layer (Penyimpanan)"]
        D1["Basis Data Relasional<br/>SQLAlchemy<br/>AdminUser<br/>KnowledgeBaseFile"]
        D2["FAISS Vector Store<br/>Document Embeddings"]
    end
    
    Backend3 -->|"SQLAlchemy ORM"| D1
    Backend4 -->|"Vector Operations"| D2
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff4e1
    style DataLayer fill:#e8f5e9
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

### 3. Start the Flask Server
```bash
python main.py
```
The server will start on `http://localhost:5000`

### 4. Access the System
- **Home:** `http://localhost:5000/`
- **Chat Interface:** `http://localhost:5000/chat`
- **Admin Dashboard:** `http://localhost:5000/admin` (requires login)

---

## Admin Dashboard

- **URL:** `/admin` (requires authentication)
- **Features:**
  - Upload documents (PDF, TXT, CSV)
  - Preview chunking before embedding
  - Embed all files to vector DB
  - Delete individual files (removes from DB and disk)
  - Delete all vector DB contents (enables re-embedding)
  - View file status and embedding progress
  - Professional UI with modern design

---

## Chat Interface

- **URL:** `/chat`
- **Features:**
  - Clean, professional chat interface
  - Markdown support for better response readability
  - Responsive design for mobile and desktop
  - Real-time chat with the RAG system

---

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/test` - System test endpoint
- `POST /api/chat` - Chat API endpoint
- `GET /api/files` - List uploaded files
- `POST /api/preview-chunking` - Preview document chunking
- `GET /api/kb_status` - Knowledge base status
- `POST /api/admin/embed_all` - Embed all files
- `GET /api/admin/embed_progress` - Embedding progress

---

## Environment Variables

Required environment variables (see `env.example`):
- `GOOGLE_API_KEY` - Google Gemini API key
- `NOMIC_API_KEY` - Nomic embeddings API key
- `JINA_API_KEY` - Jina reranking API key
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - Database connection string (defaults to SQLite)

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
- Admin authentication required for sensitive operations
- Regularly update dependencies

---

## Troubleshooting

- **Vector store not found:**
  - Upload files through the admin dashboard and click "Embed Data"
- **API key errors:**
  - Check your `.env` file for correct keys
- **Admin login issues:**
  - Run `python main.py init-db` to create admin user
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

This chatbot is designed for the Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta, with support for Indonesian language, local document retrieval, and a professional web interface for knowledge base management.

---

## Recent Updates

- ✅ **Professional UI Design** - Modern, responsive interface with Tailwind CSS
- ✅ **Admin Authentication** - Secure login system for admin dashboard
- ✅ **File Management** - Upload, preview, embed, and delete documents
- ✅ **Jina Reranking** - Top 3 document reranking for better responses
- ✅ **Markdown Support** - Enhanced chat response readability
- ✅ **Mobile Responsive** - Optimized for all device sizes 
