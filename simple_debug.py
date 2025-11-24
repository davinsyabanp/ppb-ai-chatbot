#!/usr/bin/env python3
"""Simple debug: check if documents reaching prompt."""

print("=" * 80)
print("SIMPLE DEBUG: TRACE DOCUMENT CHAIN")
print("=" * 80)

try:
    from app.core import create_rag_chain, hybrid_retrieve
    
    # Create RAG chain
    print("\nCreating RAG chain...")
    rag_chain, vector_store, embeddings, document_chain = create_rag_chain()
    
    # Get context
    query = "Apa saja layanan yang tersedia?"
    print(f"Retrieving context for: '{query}'")
    hybrid_docs = hybrid_retrieve(query, vector_store, embeddings, top_k=6)
    context_docs = [
        doc
        for doc in hybrid_docs
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str)
    ]
    
    print(f"Found {len(context_docs)} context docs")
    print(f"Docs to send: {context_docs[:2]}")
    
    # Try invoke with full logging
    print("\nInvoking document_chain with context...")
    input_data = {"input": query, "documents": context_docs[:5]}
    
    # Check each step manually
    print(f"\nStep-by-step:")
    print(f"1. Input docs count: {len(input_data['documents'])}")
    for i, doc in enumerate(input_data['documents'][:2]):
        content = doc.page_content[:60] if hasattr(doc, 'page_content') else str(doc)[:60]
        print(f"   Doc {i}: {content}...")
    
    print(f"2. Invoking chain...")
    result = document_chain.invoke(input_data)
    
    print(f"3. Result:")
    print(f"   Type: {type(result)}")
    print(f"   Content: {result}")
    
    if "tidak ditemukan" in result.lower():
        print(f"\n*** LLM returned 'not found' despite having {len(context_docs)} docs ***")
        print(f"*** This suggests LLM is ignoring context or instruction ***")
        
except Exception as e:
    import traceback
    print(f'\nError: {e}')
    traceback.print_exc()

print("\n" + "=" * 80)
