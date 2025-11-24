from typing import Dict, List, Optional, Tuple, Any
from .langchain_compat import (
    ChatPromptTemplate,
    create_stuff_documents_chain,
    create_retrieval_chain,
)
from .models import load_llm, load_embedding_model
from .vector_store import load_vector_store, hybrid_retrieve
import os
import traceback
import re
import threading
from app.models import KnowledgeBaseFile, db
from app.vector_store import create_vector_store
from langchain_community.document_loaders import PyMuPDFLoader
from .langchain_compat import Document, RecursiveCharacterTextSplitter
import pandas as pd  # type: ignore
import hashlib

# Store user sessions to track new users
user_sessions: Dict[str, bool] = {}

# Track last context for each user for clarification
last_context: Dict[str, Tuple[List[Document], str]] = {}

embedding_progress: Dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "total": 0,
    "current": 0,
    "message": "",
}

def create_rag_chain():
    """vis
    Create and return a RAG chain with LLM, embeddings, and vector store.
    Returns:
        Tuple: Configured RAG chain components
    """
    # Load models
    llm = load_llm()
    embeddings = load_embedding_model()
    
    # Load vector store
    vector_store = load_vector_store(embeddings)
    if not vector_store:
        raise ValueError("Vector store not found. Please run ingest.py first.")
    # Use a dummy retriever, we'll override retrieval below
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 1}
    )
    # SINGLE authoritative prompt for all responses
    prompt = ChatPromptTemplate.from_template(
        """Anda adalah Asisten Virtual profesional, ramah, dan ahli untuk Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta. Tugas Anda adalah menjawab pertanyaan berdasarkan informasi yang diberikan dalam <context> berikut.

### ATURAN MUTLAK:
1. *Selalu jawab dalam Bahasa Indonesia yang baik, sopan, dan profesional.*
2. *Gunakan hanya informasi dari <context> untuk menjawab.*
3. *JANGAN PERNAH mengulang atau menulis ulang kalimat, poin, atau informasi apapun.*
4. *Gabungkan dan sintesis informasi dari <context> menjadi jawaban yang mengalir, jelas, dan mudah dipahami.*
5. *Gunakan format Markdown:*
   - Gunakan heading (###, ####) untuk judul dan subjudul.
   - Gunakan bullet list (*) dan numbered list (1.) sesuai kebutuhan.
   - Gunakan *bold* untuk kata kunci penting.
6. *Jika informasi tidak ditemukan di <context>, jawab dengan kalimat standar:*
   - "Maaf, informasi mengenai hal tersebut tidak ditemukan dalam basis pengetahuan saya."
7. *Akhiri setiap jawaban dengan pertanyaan ramah untuk mendorong interaksi lanjutan.*
8. *Jangan pernah menyalin mentah dari <context>; selalu parafrase dan rangkum.*

<context>
{documents}
</context>

*Pertanyaan Pengguna:*
{input}

"""
    )
    
    # Create document chain
    document_chain = create_stuff_documents_chain(
        llm=llm, prompt=prompt, document_variable_name="documents"
    )
    
    # Create retrieval chain
    rag_chain = create_retrieval_chain(
        retriever=retriever, combine_docs_chain=document_chain
    )
    
    return rag_chain, vector_store, embeddings, document_chain


def is_new_user(user_id: str) -> bool:
    """
    Check if user is new based on their ID.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        bool: True if user is new, False otherwise
    """
    return user_id not in user_sessions


def mark_user_as_known(user_id: str) -> None:
    """
    Mark user as known (not new anymore).
    
    Args:
        user_id (str): User identifier
    """
    user_sessions[user_id] = True


def format_bot_response(answer: str) -> str:
    """
    Minimal post-processing: strip whitespace, remove XML tags, and ensure a friendly closing if missing.
    """
    # Remove leading/trailing whitespace and normalize line breaks
    answer = answer.strip().replace("\r\n", "\n").replace("\r", "\n")
    # Remove any leftover <context>...</context> tags
    answer = re.sub(r"<context>[\s\S]*?</context>", "", answer, flags=re.IGNORECASE).strip()
    # Optionally, add a friendly closing if not present
    if not re.search(r"\?\s*$", answer):
        answer += "\n\nApakah ada pertanyaan lain yang bisa saya bantu? 😊"
    return answer


def get_response(query: str, user_id: Optional[str] = None, conversation_has_started: bool = False, is_initial_greeting_sent: bool = False) -> str:
    """
    Get a response from the RAG chain for a given query, with robust follow-up logic for elaboration requests.
    Args:
        query (str): The user's question
        user_id (Optional[str]): User identifier for session tracking
    Returns:
        str: The AI's response in Indonesian
    """
    try:
        # Handle empty or greeting queries
        query_lower = query.lower().strip()
        if not query or query_lower in [
            "hi",
            "hello",
            "halo",
            "hai",
            "selamat pagi",
            "selamat siang",
            "selamat malam",
        ]:
            return format_bot_response(
                "Halo! 👋 \n\nSelamat datang di Asisten Virtual Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta. \n\n"
                "UIN Syarif Hidayatullah Jakarta. \n\n"
                "Saya siap membantu Anda dengan informasi seputar Pusat Pengembangan Bahasa (PPB). \n\n"
                "Silakan ajukan pertanyaan spesifik tentang informasi yang "
                "Anda butuhkan! 😊"
            )

        # Check if this is a new user
#         if user_id and is_new_user(user_id):
#             mark_user_as_known(user_id)
#             return format_bot_response(
#                 """Selamat datang di Asisten Virtual Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta! 🎓

# Saya adalah asisten AI yang siap membantu Anda dengan informasi seputar layanan di Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta.

# *Layanan yang tersedia:*
# • Informasi jadwal dan pendaftaran tes TOAFL/TOEFL
# • Kursus bahasa (Inggris, Arab, dll)
# • Layanan penerjemahan dan proofreading
# • Informasi biaya, lokasi, dan kontak PPB
# • Frequently Asked Questions (FAQ)

# *Catatan:* Saya akan memberikan jawaban berdasarkan dokumen resmi PPB UIN Jakarta. Untuk informasi yang lebih spesifik, silakan hubungi langsung administrasi PPB.

# Silakan ajukan pertanyaan Anda! 😊"""
#             )
        
        # Robust follow-up trigger detection
        followup_triggers = [
            "jelaskan lebih lanjut",
            "jelaskan lebih detail",
            "jelaskan lebih jelas",
            "jelaskan lebih rinci",
            "jelaskan lebih lengkap",
            "saya ingin penjelasan lebih lanjut",
            "explain more",
            "can you elaborate",
            "give me more details",
            "be more specific",
            "tell me more about that",
            "in more detail, please",
            "elaborate on that",
        ]
        if user_id and any(query_lower.startswith(trigger) for trigger in followup_triggers):
            if user_id in last_context:
                context_docs, last_question = last_context[user_id]
                valid_context = (
                    isinstance(context_docs, list)
                    and context_docs
                    and hasattr(context_docs[0], "page_content")
                )
                if not valid_context:
                    return format_bot_response(
                        "Maaf, tidak ada topik sebelumnya yang dapat dijelaskan lebih lanjut. Silakan ajukan pertanyaan baru."
                    )
                # Formulate a detail-enhancing query
                detail_query = (
                    f"Terkait pertanyaan saya sebelumnya, '{last_question}', "
                    "mohon berikan penjelasan yang jauh lebih rinci dan komprehensif. "
                    "Jabarkan semua poin penting, sertakan langkah-langkah atau contoh lebih spesifik jika tersedia dari konteks, dan pastikan jawabannya selengkap mungkin."
                )
                # Use the same context_docs, do NOT re-retrieve
                rag_chain, vector_store, embeddings, document_chain = create_rag_chain()
                answer = document_chain.invoke({"input": detail_query, "documents": context_docs[:5]})
                if not answer or answer.strip() == "":
                    return format_bot_response(
                        "Maaf, saya tidak dapat memberikan penjelasan lebih lanjut. Silakan ajukan pertanyaan lain."
                    )
                # Do NOT update last_context here (keep the original question for further follow-ups)
                return format_bot_response(answer)
            else:
                return format_bot_response(
                    "Maaf, tidak ada topik sebelumnya yang dapat dijelaskan lebih lanjut. Silakan ajukan pertanyaan baru."
                )
        
        # Create RAG chain
        rag_chain, vector_store, embeddings, document_chain = create_rag_chain()
        
        # Hybrid retrieval
        hybrid_docs = hybrid_retrieve(query, vector_store, embeddings, top_k=6)
        context_docs = [
            doc
            for doc in hybrid_docs
            if hasattr(doc, "page_content") and isinstance(doc.page_content, str)
        ]
        if user_id:
            last_context[user_id] = (context_docs, query)
        if not context_docs:
            return format_bot_response(
                "Maaf, informasi mengenai hal tersebut tidak ditemukan dalam basis pengetahuan saya."
            )

        # Use the main RAG chain and authoritative prompt
        answer = document_chain.invoke({"input": query, "documents": context_docs[:5]})
        if not answer or answer.strip() == "":
            return format_bot_response(
                "Maaf, informasi mengenai hal tersebut tidak ditemukan dalam basis pengetahuan saya."
            )
        return format_bot_response(answer)
    
    except Exception as e:
        print("=== FULL TRACEBACK ===")
        traceback.print_exc()
        print("=== END TRACEBACK ===")
        error_msg = (
            f"Maaf, saya mengalami kesalahan dalam memproses "
            f"pertanyaan Anda: {str(e)}"
        )
        return format_bot_response(error_msg)


def get_system_info() -> str:
    """
    Get information about the system and available documents.
    
    Returns:
        str: System information in Indonesian
    """
    try:
        embeddings = load_embedding_model()
        vector_store = load_vector_store(embeddings)
        
        if not vector_store:
            return (
                "Sistem Customer Service belum siap. Silakan jalankan "
                "ingest.py terlebih dahulu untuk memproses dokumen."
            )
        
        # Get document count and types
        docs_dir = "documents"
        if os.path.exists(docs_dir):
            files = [
                f for f in os.listdir(docs_dir) if f.endswith((".pdf", ".txt", ".csv"))
            ]
            file_types: Dict[str, int] = {}
            for file in files:
                ext = file.split(".")[-1].upper()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            info = (
                "🎓 Asisten Virtual Pusat Pengembangan Bahasa (PPB) UIN Syarif Hidayatullah Jakarta\n\n"
            )
            info += f"Sistem siap dengan {len(files)} dokumen layanan PPB:\n"
            for ext, count in file_types.items():
                info += f"• {count} file {ext}\n"
            info += "\n📚 Dokumen yang tersedia:\n"
            info += "• Profil Pusat Pengembangan Bahasa (PPB)\n"
            info += "• Jadwal & Pendaftaran Tes TOAFL/TOEFL\n"
            info += "• Kursus Bahasa (Inggris, Arab, dll)\n"
            info += "• Layanan Penerjemahan & Proofreading\n"
            info += "• Frequently Asked Questions (FAQ)\n"
            info += "• Informasi Biaya, Lokasi, dan Kontak PPB\n"
            return info
        else:
            return "Tidak ada dokumen yang ditemukan."
            
    except Exception as e:
        return f"Error getting system info: {str(e)}"


def load_kb_files() -> List[Document]:
    """
    Load all knowledge base files from the database and return as Document objects.
    """
    documents: List[Document] = []
    files = KnowledgeBaseFile.query.all()
    for kb_file in files:
        try:
            if kb_file.filetype == "pdf":
                loader = PyMuPDFLoader(kb_file.filepath)
                docs = loader.load()
                for d in docs:
                    d.metadata["file_type"] = "pdf"
                documents.extend(docs)
            elif kb_file.filetype == "txt":
                with open(kb_file.filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={"source": kb_file.filename, "file_type": "txt"},
                        )
                    )
            elif kb_file.filetype == "csv":
                df = pd.read_csv(kb_file.filepath)
                for index, row in df.iterrows():
                    row_text = ""
                    for column, value in row.items():
                        if pd.notna(value):
                            row_text += f"{column}: {value}\n"
                    if row_text.strip():
                        metadata = {
                            "source": kb_file.filename,
                            "row": int(str(index)) + 1,
                            "file_type": "csv",
                        }
                        documents.append(
                            Document(page_content=row_text.strip(), metadata=metadata)
                        )
        except Exception as e:
            print(f"Error loading {kb_file.filename}: {e}")
    return documents


def split_documents_by_type(
    documents: List[Document], chunk_size: int = 2000, chunk_overlap: int = 400
) -> List[Document]:
    csv_docs = [doc for doc in documents if doc.metadata.get("file_type") == "csv"]
    pdf_docs = [doc for doc in documents if doc.metadata.get("file_type") == "pdf"]
    txt_docs = [doc for doc in documents if doc.metadata.get("file_type") == "txt"]
    chunks: List[Document] = []
    if csv_docs:
        csv_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks.extend(csv_splitter.split_documents(csv_docs))
    if pdf_docs:
        pdf_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks.extend(pdf_splitter.split_documents(pdf_docs))
    if txt_docs:
        txt_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks.extend(txt_splitter.split_documents(txt_docs))
    return chunks


def get_changed_files() -> List[KnowledgeBaseFile]:
    """
    Return a list of KnowledgeBaseFile objects whose file hash does not match
    the current file content.
    """
    changed: List[KnowledgeBaseFile] = []
    files = KnowledgeBaseFile.query.all()
    for kb_file in files:
        try:
            with open(kb_file.filepath, "rb") as f:
                filehash = hashlib.sha256(f.read()).hexdigest()
            if filehash != kb_file.filehash:
                changed.append(kb_file)
        except Exception:
            # If file missing or unreadable, treat as changed
            changed.append(kb_file)
    return changed


def run_embedding_background(app: Any, force_all: bool = False) -> None:
    global embedding_progress
    with app.app_context():
        embedding_progress["status"] = "running"
        embedding_progress["progress"] = 0
        embedding_progress["message"] = "Loading documents..."
        if force_all:
            files = KnowledgeBaseFile.query.all()
        else:
            files = get_changed_files()
        total = len(files)
        embedding_progress["total"] = total
        embedding_progress["current"] = 0
        if total == 0:
            embedding_progress["status"] = "done"
            embedding_progress["progress"] = 100
            embedding_progress["message"] = "No files need re-embedding."
            return
        # Load and split only the selected files
        documents: List[Document] = []
        for kb_file in files:
            try:
                if kb_file.filetype == "pdf":
                    loader = PyMuPDFLoader(kb_file.filepath)
                    docs = loader.load()
                    for d in docs:
                        d.metadata["file_type"] = "pdf"
                    documents.extend(docs)
                elif kb_file.filetype == "txt":
                    with open(kb_file.filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        documents.append(
                            Document(
                                page_content=text,
                                metadata={
                                    "source": kb_file.filename,
                                    "file_type": "txt",
                                },
                            )
                        )
                elif kb_file.filetype == "csv":
                    df = pd.read_csv(kb_file.filepath)
                    for index, row in df.iterrows():
                        row_text = ""
                        for column, value in row.items():
                            if pd.notna(value):
                                row_text += f"{column}: {value}\n"
                        if row_text.strip():
                            metadata = {
                                "source": kb_file.filename,
                                "row": int(str(index)) + 1,
                                "file_type": "csv",
                            }
                            documents.append(
                                Document(
                                    page_content=row_text.strip(), metadata=metadata
                                )
                            )
            except Exception as e:
                print(f"Error loading {kb_file.filename}: {e}")
            embedding_progress["current"] += 1
            embedding_progress["progress"] = int(
                (embedding_progress["current"]) / total * 100
            )
        embedding_progress["message"] = "Splitting documents..."
        chunks = split_documents_by_type(documents, chunk_size=2000, chunk_overlap=400)
        embedding_progress["message"] = "Creating vector store..."
        create_vector_store(chunks)
        # Update hashes in DB for changed files
        for kb_file in files:
            try:
                with open(kb_file.filepath, "rb") as f:
                    kb_file.filehash = hashlib.sha256(f.read()).hexdigest()
                db.session.commit()
            except Exception:
                pass
        embedding_progress["progress"] = 100
        embedding_progress["status"] = "done"
        embedding_progress["message"] = "Embedding complete!"


def start_embedding(app: Any, force_all: bool = False) -> bool:
    """
    Start the embedding process in a background thread.
    """
    global embedding_progress
    if embedding_progress["status"] == "running":
        return False  # Already running
    embedding_progress["status"] = "starting"
    thread = threading.Thread(target=run_embedding_background, args=(app, force_all))
    thread.start()
    return True


def get_embedding_progress() -> Dict[str, Any]:
    """
    Return the current embedding progress as a dict.
    """
    global embedding_progress
    return embedding_progress


def get_file_status() -> List[Dict[str, Any]]:
    """
    Return a list of dicts with file info and changed status for dashboard display.
    """
    files = KnowledgeBaseFile.query.all()
    changed_ids = {f.id for f in get_changed_files()}
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "filetype": f.filetype,
            "uploaded_at": f.uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "changed": f.id in changed_ids,
        }
        for f in files
    ]


def get_response_for_evaluation(query: str, user_id: str = "evaluation_user") -> Dict[str, Any]:
    """
    Get a response and the context documents for evaluation purposes.
    Args:
        query (str): The user's question.
        user_id (str): The user ID to use for context (default: 'evaluation_user').
    Returns:
        Dict[str, Any]: A dictionary containing the query, answer, and context documents.
    """
    try:
        # Create RAG chain components
        rag_chain, vector_store, embeddings, document_chain = create_rag_chain()

        # Hybrid retrieval
        hybrid_docs = hybrid_retrieve(query, vector_store, embeddings, top_k=5)
        context_docs = [
            doc
            for doc in hybrid_docs
            if hasattr(doc, "page_content") and isinstance(doc.page_content, str)
        ]

        if not context_docs:
            return {
                "question": query,
                "answer": "Maaf, informasi mengenai hal tersebut tidak ditemukan dalam basis pengetahuan saya.",
                "contexts": []
            }

        # Invoke the document chain to get the answer
        answer = document_chain.invoke({"input": query, "documents": context_docs})

        # Format the response and return all components
        formatted_answer = format_bot_response(answer)
        context_strings = [doc.page_content for doc in context_docs]

        return {
            "question": query,
            "answer": formatted_answer,
            "contexts": context_strings
        }

    except Exception as e:
        print(f"Error during evaluation response generation: {e}")
        return {
            "query": query,
            "answer": f"Error: {str(e)}",
            "contexts": []
        }