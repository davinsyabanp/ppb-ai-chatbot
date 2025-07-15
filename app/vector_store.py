import os
from langchain_community.vectorstores import FAISS
from .models import load_embedding_model
from langchain.schema import Document
from typing import List
import re
import requests
import html

def create_vector_store(chunks):
    """
    Create a FAISS vector store from document chunks and save it to disk.
    
    Args:
        chunks: List of document chunks to embed and store
    """
    # Load the embedding model
    embeddings = load_embedding_model()
    
    # Create FAISS vector store from documents
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    
    # Create directory if it doesn't exist
    os.makedirs("vector_db", exist_ok=True)
    
    # Save the vector store to disk
    vector_store.save_local("vector_db/faiss_index")
    print("Vector store created and saved successfully.")

def load_vector_store(embeddings):
    """
    Load an existing FAISS vector store from disk.
    
    Args:
        embeddings: Embedding model instance (Embeddings object)
        
    Returns:
        FAISS: Loaded vector store instance or None if not found
    """
    index_path = "vector_db/faiss_index"
    
    if os.path.exists(index_path):
        try:
            vector_store = FAISS.load_local(
                folder_path=index_path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True  # Enable for trusted local files
            )
            print("Vector store loaded successfully.")
            # Diagnostic: print types of all docstore values
            doc_types = {}
            for i, doc in enumerate(vector_store.docstore._dict.values()):
                t = type(doc).__name__
                doc_types[t] = doc_types.get(t, 0) + 1
                if not hasattr(doc, 'page_content'):
                    print(f"[DOCSTORE-DEBUG] Non-Document object at index {i}: {t}: {repr(doc)[:100]}")
            print(f"[DOCSTORE-DEBUG] Docstore object type counts: {doc_types}")
            return vector_store
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return None
    else:
        print("Vector store not found. Please run ingest.py first.")
        return None

def simple_full_text_search(query: str, documents: List[Document], top_k: int = 4) -> List[Document]:
    """
    Simple keyword-based full-text search over documents.
    Returns top_k documents with the most keyword matches.
    """
    query_keywords = set(re.findall(r'\w+', query.lower()))
    scored_docs = []
    for doc in documents:
        content = doc.page_content.lower()
        score = sum(1 for word in query_keywords if word in content)
        if score > 0:
            scored_docs.append((score, doc))
    # Sort by score descending
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    return [doc for score, doc in scored_docs[:top_k]]

def rerank_documents_with_jina(query: str, docs: List[Document], top_k: int = 6) -> List[Document]:
    """
    Use Jina AI Rerank API (v2 multilingual) to rerank the documents by relevance to the query.
    Requires JINA_API_KEY in environment.
    """
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("[JINA-RERANK] No JINA_API_KEY set, skipping rerank.")
        return docs[:top_k]
    if not query or not isinstance(query, str) or not query.strip():
        print("[JINA-RERANK] Query is empty or not a string, skipping rerank.")
        return docs[:top_k]
    if not docs:
        print("[JINA-RERANK] No documents to rerank, skipping rerank.")
        return []

    # Clean and deduplicate documents
    seen = set()
    clean_docs = []
    doc_map = []
    for idx, doc in enumerate(docs):
        if not hasattr(doc, "page_content"):
            continue
        content = doc.page_content
        if not isinstance(content, str):
            continue
        content = content.strip()
        if not content:
            continue
        # Truncate to 4096 chars
        content = html.unescape(content[:4096])
        if content in seen:
            continue
        seen.add(content)
        clean_docs.append(content)
        doc_map.append(idx)
    if not clean_docs:
        print("[JINA-RERANK] All documents empty after cleaning, skipping rerank.")
        return []
    # Jina API allows max 20 docs per request
    clean_docs = clean_docs[:20]
    doc_map = doc_map[:20]
    endpoint = "https://api.jina.ai/v1/rerank"
    payload = {
        "query": query.strip(),
        "documents": clean_docs,
        "model": "jina-reranker-v2-base-multilingual",
        "top_n": min(top_k, len(clean_docs))
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        if "results" in result:
            indices = [r["index"] for r in result["results"]]
            reranked = [docs[doc_map[i]] for i in indices if i < len(doc_map)]
            print(f"[JINA-RERANK] Reranked top {len(reranked)} docs (v2 multilingual).")
            return reranked
        else:
            print(f"[JINA-RERANK] Unexpected response: {result}")
            return docs[:top_k]
    except Exception as e:
        print(f"[JINA-RERANK] Error: {e}")
        return docs[:top_k]

def hybrid_retrieve(query: str, vector_store, embeddings, top_k: int = 6) -> List[Document]:
    """
    Hybrid retrieval: combine semantic (vector) and full-text (keyword) search.
    Returns the most relevant documents from both methods (no duplicates).
    """
    # Semantic search (filter only Document objects)
    semantic_docs = []
    for doc in vector_store.similarity_search(query, k=top_k):
        if hasattr(doc, 'page_content'):
            semantic_docs.append(doc)
        else:
            print(f"[DEBUG] semantic_docs: Skipping non-Document object: {type(doc)}: {repr(doc)[:100]}")
    # Full-text search (over all docs in the store, filter only Document objects)
    all_docs = []
    for doc in vector_store.docstore._dict.values():
        if hasattr(doc, 'page_content'):
            all_docs.append(doc)
        else:
            print(f"[DEBUG] all_docs: Skipping non-Document object: {type(doc)}: {repr(doc)[:100]}")
    fulltext_docs = []
    for doc in simple_full_text_search(query, all_docs, top_k=top_k):
        if hasattr(doc, 'page_content'):
            fulltext_docs.append(doc)
        else:
            print(f"[DEBUG] fulltext_docs: Skipping non-Document object: {type(doc)}: {repr(doc)[:100]}")
    # Combine, remove duplicates (by content)
    seen = set()
    hybrid_docs = []
    for doc in semantic_docs + fulltext_docs:
        if not hasattr(doc, 'page_content'):
            print(f"[DEBUG] hybrid_docs: Skipping non-Document object: {type(doc)}: {repr(doc)[:100]}")
            continue
        key = doc.page_content.strip()
        if key not in seen:
            hybrid_docs.append(doc)
            seen.add(key)
    # Rerank with Jina if API key is set
    hybrid_docs = rerank_documents_with_jina(query, hybrid_docs, top_k=top_k)
    return hybrid_docs[:top_k] 