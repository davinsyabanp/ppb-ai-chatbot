# RAG Chatbot with Google Gemini

A Retrieval-Augmented Generation (RAG) chatbot that answers questions based on local documents, accessible via a web chat interface. Powered by Google Gemini Pro and local FAISS vector store.

## Features

- 🤖 **RAG-powered responses** based on local document knowledge base
- 🧠 **Google Gemini** for text generation
- 🔍 **Local embeddings** using nomic-embed-text model
- 📚 **FAISS vector store** for efficient document retrieval
- 📄 **Multi-format support** (PDF, TXT, CSV documents)
- 📊 **CSV processing** with row-by-row conversion for structured data

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Twilio        │    │   Flask App     │
│   (User)        │───▶│   Gateway       │───▶│   (Webhook)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Google        │    │   Ollama        │    │   FAISS         │
│   Gemini Pro    │◀───│   Embeddings    │◀───│   Vector Store  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

1. **Python 3.8+**
2. **Nomic API key** with `nomic-embed-text:v1.5` model
3. **Google AI Studio API key**
4. **Twilio account** with WhatsApp sandbox

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd rag-chatbot-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp env.example .env
   ```
   Edit `.env` with your credentials:
   ```env
   GOOGLE_API_KEY="your_google_api_key_here"
   NOMIC_API_KEY= "yout_nomic_api_key_here"
   ```

## Setup Instructions

### 1. Add Documents
Place your source documents (PDF, TXT, CSV) in the `documents/` folder.

**Supported formats:**
- **PDF files** (.pdf) - Extracted text content
- **Text files** (.txt) - Plain text content
- **CSV files** (.csv) - Structured data converted to text format

### 2. Create Vector Store
```bash
python ingest.py
```
This will:
- Load documents from the `documents/` folder
- Process CSV files row by row (each row becomes a document chunk)
- Split them into chunks
- Create embeddings using Nomic
- Save the FAISS vector store to `vector_db/`

### 3. Start the Flask Server
```bash
python main.py
```
The server will start on `http://localhost:5000`

## Usage

1. **Upload documents** via the web interface
2. **Ask questions** about the content in your documents
3. **Receive AI-powered responses** based on your knowledge base

**Example questions for CSV data:**
- "Who works in the Engineering department?"
- "What is Jane Smith's position?"
- "How many employees are there?"
- "What departments do we have?"

## Project Structure

```
rag-chatbot-ai/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── models.py            # LLM and embedding model initialization
│   ├── core.py              # RAG chain logic
│   └── vector_store.py      # FAISS vector store operations
├── documents/               # Source documents folder
├── main.py                  # Flask web server
├── ingest.py                # Document processing script
├── setup.py                 # Setup and testing script
├── requirements.txt         # Python dependencies
├── env.example              # Environment variables template
└── README.md                # This file
```

## API Endpoints

- `GET /` - Home page with basic information
- `GET /health` - Health check endpoint
- `GET /chat` - Web chat interface

## Development

### Local Development
For local development, simply run:
```bash
python main.py
```

### Testing
You can test the RAG functionality directly:
```python
from app.core import get_response
response = get_response("What is the main topic of your documents?")
print(response)
```

## CSV Processing Details

CSV files are processed with the following features:
- **Row-by-row processing**: Each row becomes a separate document chunk
- **Column-value format**: Data is converted to "column: value" text format
- **Metadata tracking**: Includes source file and row number information
- **Empty value handling**: Skips NaN or empty values
- **Searchable content**: All CSV data becomes searchable through the RAG system

**Example CSV input:**
```csv
Name,Age,Department
John Doe,30,Engineering
Jane Smith,28,Marketing
```

**Becomes searchable as:**
```
Name: John Doe
Age: 30
Department: Engineering
```

## Troubleshooting

### Common Issues

1. **Vector store not found:**
   - Run `python ingest.py` to create the vector store
   - Ensure documents are in the `documents/` folder

2. **Google API key error:**
   - Verify your API key in the `.env` file
   - Check if the key has proper permissions

3. **CSV processing errors:**
   - Ensure CSV files are properly formatted
   - Check for encoding issues (UTF-8 recommended)
   - Verify pandas is installed: `pip install pandas`

## Security Considerations

- Keep your API keys secure and never commit them to version control
- Use HTTPS in production
- Regularly update dependencies

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Customer Service Teknik Informatika UIN Jakarta

Chatbot AI ini dirancang khusus untuk Customer Service Program Studi Teknik Informatika UIN Syarif Hidayatullah Jakarta.

### Layanan yang Tersedia:
- 📚 Informasi kurikulum dan mata kuliah
- 🎓 Panduan akademik dan administrasi  
- 👨‍🏫 Informasi dosen dan jadwal
- 📝 Bantuan pendaftaran dan registrasi
- 📋 Panduan PKL dan skripsi

### Akses Melalui:

#### Web Chat Interface
- Buka browser dan akses: `http://localhost:5000/chat`
- Antarmuka web yang responsif dan mudah diakses dari perangkat apa pun
- Desain modern mirip ChatGPT/DeepSeek

### Contoh Pertanyaan:
- "Bagaimana struktur kurikulum semester 1?"
- "Siapa saja dosen pengajar mata kuliah [nama mata kuliah]?"
- "Bagaimana prosedur pendaftaran PKL?"
- "Apa saja persyaratan untuk skripsi?"
- "Informasi tentang mata kuliah pilihan"

## 🚀 Deployment on Render (Free Tier)

1. **Create a Render.com account** (https://render.com/)
2. **Create a new Web Service** and connect your GitHub repo.
3. **Set environment variables** in the Render dashboard:
   - `SECRET_KEY` (any random string)
   - `DATABASE_URL` (default: `sqlite:///app.db`)
   - `GOOGLE_API_KEY`, etc. (as needed for your LLM/embedding)
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `python main_whatsapp.py`
6. **Persistent Disk:** Enable if you want to keep uploaded files and vector DB.
7. **Access your app** via the provided Render URL.

**Note:** For production, consider using PostgreSQL (Render offers a free tier) and update `DATABASE_URL` accordingly. 