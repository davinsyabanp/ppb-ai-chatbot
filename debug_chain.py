#!/usr/bin/env python3
"""Debug document chain and prompt."""

print("=" * 60)
print("DEBUGGING DOCUMENT CHAIN & PROMPT")
print("=" * 60)

try:
    from app.core import create_rag_chain, hybrid_retrieve
    from app.models import load_embedding_model
    from app.vector_store import load_vector_store
    
    # Create RAG chain
    print("\n1. Creating RAG chain...")
    rag_chain, vector_store, embeddings, document_chain = create_rag_chain()
    print(f"   Document chain type: {type(document_chain)}")
    print(f"   Document chain: {document_chain}")
    
    # Get context
    query = "Apa saja layanan yang tersedia?"
    print(f"\n2. Retrieving context for: '{query}'")
    hybrid_docs = hybrid_retrieve(query, vector_store, embeddings, top_k=6)
    context_docs = [
        doc
        for doc in hybrid_docs
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str)
    ]
    print(f"   Found {len(context_docs)} docs")
    for i, doc in enumerate(context_docs[:3]):
        content = doc.page_content[:80] if hasattr(doc, 'page_content') else str(doc)[:80]
        print(f"   {i+1}. {content}...")
    
    # Invoke document chain
    print(f"\n3. Invoking document_chain...")
    print(f"   Input: {{'input': '{query}', 'documents': {len(context_docs[:5])} docs}}")
    
    try:
        answer = document_chain.invoke({"input": query, "documents": context_docs[:5]})
        print(f"   Response type: {type(answer)}")
        print(f"   Response: {repr(answer[:200])}")
        print(f"   Empty? {not answer or answer.strip() == ''}")
    except Exception as e:
        print(f"   ❌ Error invoking chain: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f'\n❌ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
