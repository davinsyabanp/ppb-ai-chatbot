#!/usr/bin/env python3
"""Test LLM direct call with context."""

from app.models import load_llm
from app.langchain_compat import ChatPromptTemplate

llm = load_llm()

# Simple prompt
prompt = ChatPromptTemplate.from_template("""Berdasarkan informasi berikut, jawab pertanyaan pengguna dalam Bahasa Indonesia.

Informasi:
{context}

Pertanyaan: {query}

Jawab dengan jelas dan ringkas.""")

# Sample context
context = """
category: Tes Bahasa
title: ETIC
description: Tes ETIC (English Test for Islamic Communication) adalah tes kemahiran bahasa Inggris. Prosedur pendaftaran dilakukan dengan mengakses tautan di bio Instagram @ppbuinjakarta.

category: Layanan Terjemahan
title: Terjemahan
description: PPB menawarkan layanan terjemahan. Untuk informasi lebih lanjut mengenai prosedur dan biaya, silakan hubungi administrasi PPB.
"""

query = "Apa saja layanan yang tersedia?"

# Create prompt message
prompt_value = prompt.format(context=context, query=query)
print("Prompt:")
print("=" * 60)
print(prompt_value)
print("=" * 60)

# Call LLM
print("\nCalling LLM...")
try:
    response = llm.invoke(prompt_value)
    print("\nResponse:")
    print(response)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
