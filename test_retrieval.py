#!/usr/bin/env python3
"""Test script to diagnose retrieval issue."""

import pandas as pd
import os

print("=" * 60)
print("CHECKING CSV FILES")
print("=" * 60)

# Check CSV files
csv_files = ['kurbas_PPB.csv', 'layanan_PPB.csv', 'umum_PPB.csv']
for f in csv_files:
    path = os.path.join('documents', f)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f'\n📄 {f}: {len(df)} rows, {len(df.columns)} columns')
        if len(df) > 0:
            print(f'Columns: {list(df.columns)}')
            print(f'First row (preview): {str(df.iloc[0, 0])[:100]}...')
        else:
            print('(empty dataframe)')
    else:
        print(f'\n❌ {f}: NOT FOUND')

print("\n" + "=" * 60)
print("TESTING VECTOR STORE & RETRIEVAL")
print("=" * 60)

try:
    from app.vector_store import load_vector_store
    from app.models import load_embedding_model
    
    embeddings = load_embedding_model()
    vector_store = load_vector_store(embeddings)
    
    if vector_store:
        # Get doc count
        try:
            doc_count = vector_store._collection.count()
            print(f'\n✅ Vector store loaded: {doc_count} documents')
        except:
            print(f'\n✅ Vector store loaded (doc count unavailable)')
        
        # Test queries
        test_queries = [
            "apa saja layanan",
            "jam operasional",
            "pendaftaran ETIC",
            "Pusat Pengembangan Bahasa"
        ]
        
        for query in test_queries:
            print(f'\n🔍 Query: "{query}"')
            results = vector_store.similarity_search(query, k=2)
            print(f'   Found: {len(results)} results')
            for i, doc in enumerate(results, 1):
                if hasattr(doc, 'page_content'):
                    content = doc.page_content[:80]
                    source = doc.metadata.get('source', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
                    print(f'   {i}. [{source}] {content}...')
                else:
                    print(f'   {i}. {str(doc)[:80]}...')
    else:
        print('\n❌ Vector store failed to load')
        
except Exception as e:
    print(f'\n❌ Error during retrieval test: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
