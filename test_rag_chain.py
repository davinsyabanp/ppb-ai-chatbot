#!/usr/bin/env python3
"""Test RAG chain end-to-end."""

print("=" * 60)
print("TESTING RAG CHAIN END-TO-END")
print("=" * 60)

try:
    from app.core import get_response
    
    test_questions = [
        "Apa saja layanan yang tersedia?",
        "Jam operasional Pusat Pengembangan Bahasa?",
        "Bagaimana cara daftar ETIC?",
        "Siapa kepala Pusat Pengembangan Bahasa?"
    ]
    
    for q in test_questions:
        print(f'\n❓ Q: "{q}"')
        answer = get_response(q)
        print(f'✅ A: {answer[:200]}...' if len(answer) > 200 else f'✅ A: {answer}')
        
except Exception as e:
    print(f'\n❌ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
