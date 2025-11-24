#!/usr/bin/env python3
"""Debug what actually gets sent to LLM."""

print("=" * 80)
print("DEBUGGING PROMPT & CONTEXT INJECTION")
print("=" * 80)

try:
    from app.core import create_rag_chain, hybrid_retrieve
    from app.langchain_compat import ChatPromptTemplate
    
    # Create RAG chain
    print("\n1. Creating RAG chain...")
    rag_chain, vector_store, embeddings, document_chain = create_rag_chain()
    
    # Get context
    query = "Apa saja layanan yang tersedia?"
    print(f"\n2. Retrieving context...")
    hybrid_docs = hybrid_retrieve(query, vector_store, embeddings, top_k=6)
    context_docs = [
        doc
        for doc in hybrid_docs
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str)
    ]
    print(f"   Found {len(context_docs)} docs")
    
    # Format documents manually to see what's being passed
    print(f"\n3. Formatting documents...")
    formatted_docs = "\n\n".join(doc.page_content for doc in context_docs[:5])
    print(f"   Formatted length: {len(formatted_docs)} chars")
    print(f"   Formatted content (first 300 chars):\n{formatted_docs[:300]}")
    
    # Create input dict
    print(f"\n4. Creating input dict...")
    input_dict = {
        "input": query,
        "documents": context_docs[:5]
    }
    
    # Try to manually process through chain steps
    print(f"\n5. Processing through chain steps...")
    
    # Step 1: Format docs (RunnableAssign)
    print(f"   Step 1 (format_docs)...")
    from app.langchain_compat import format_docs
    formatted = format_docs(context_docs[:5])
    print(f"   Output: {len(formatted)} chars, starts with: {formatted[:100]}...")
    
    # Create input after assign
    assigned_input = {"input": query, "documents": formatted}
    print(f"   After assign: {len(str(assigned_input))} chars")
    
    # Step 2: Format through prompt
    print(f"\n   Step 2 (ChatPromptTemplate)...")
    # Extract prompt from chain
    prompt = None
    for step in document_chain.steps:
        if isinstance(step, ChatPromptTemplate):
            prompt = step
            break
    
    if prompt:
        formatted_prompt = prompt.format_prompt(input=query, documents=formatted)
        prompt_text = formatted_prompt.to_string()
        print(f"   Prompt length: {len(prompt_text)} chars")
        print(f"   Prompt (first 400 chars):\n{prompt_text[:400]}")
        print(f"   ... [middle] ...")
        print(f"   Prompt (last 200 chars):\n{prompt_text[-200:]}")
    
    print(f"\n6. Direct LLM call test...")
    from app.models import load_llm
    llm = load_llm()
    if prompt:
        result = llm.invoke(formatted_prompt)
        print(f"   LLM Result: {result}")
        print(f"   LLM Result (first 300 chars): {str(result)[:300]}")
    
except Exception as e:
    print(f'\n❌ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
