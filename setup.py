#!/usr/bin/env python3
"""
Setup script for RAG Chatbot AI - Indonesian Version
This script helps you set up and test the bot.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 atau lebih tinggi diperlukan")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} terdeteksi")
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ File .env tidak ditemukan")
        print("Silakan salin env.example ke .env dan isi API key Anda:")
        print("cp env.example .env")
        return False
    
    # Check for required variables
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if f'{var}=' not in content or 'ENTER_YOUR' in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variabel environment yang hilang atau tidak lengkap: {', '.join(missing_vars)}")
        print("Silakan update file .env dengan nilai yang benar")
        return False
    
    print("✅ Variabel environment dikonfigurasi")
    return True

def install_dependencies():
    """Install Python dependencies."""
    try:
        print("📦 Menginstal dependensi Python...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependensi berhasil diinstal")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error menginstal dependensi: {e}")
        return False

def create_vector_store():
    """Create the vector store from documents."""
    try:
        print("📚 Membuat vector store...")
        subprocess.run([sys.executable, 'ingest.py'], check=True)
        print("✅ Vector store berhasil dibuat")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error membuat vector store: {e}")
        return False

def test_rag():
    """Test the RAG functionality with Indonesian questions."""
    try:
        print("🧪 Menguji fungsi RAG dengan pertanyaan Bahasa Indonesia...")
        from app.core import get_response, get_system_info
        
        # Test system info
        system_info = get_system_info()
        print(f"✅ Info sistem: {system_info}")
        
        # Test with Indonesian questions
        test_questions = [
            "Siapa kepala Pusat Pengembangan Bahasa?",
            "Jam Operasional Pusat Pengembangan Bahasa?",
            "Apa saja layanan yang tersedia di Pusat Pengembangan Bahasa?",
            "Bagaimana prosedur pendaftaran ETIC?"
        ]
        
        for question in test_questions:
            response = get_response(question)
            print(f"✅ Pertanyaan: {question}")
            print(f"   Jawaban: {response[:100]}...")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Error menguji pipeline RAG: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setup RAG Bot - Versi Indonesia")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check environment variables
    if not check_env_file():
        return False
    
    # Create vector store
    if not create_vector_store():
        return False
    
    # Test RAG
    if not test_rag():
        return False
    
    print("\n🎉 Setup berhasil diselesaikan!")
    print("\nFitur yang tersedia:")
    print("✅ Respons dalam Bahasa Indonesia")
    print("✅ Pesan selamat datang untuk pengguna baru")
    print("✅ Perintah khusus (/info, /help)")
    print("✅ Tracking sesi pengguna")
    print("✅ Dukungan dokumen PDF, TXT, dan CSV")
    
    print("\nLangkah selanjutnya:")
    print("1. Jalankan server: python main.py")
    print("2. Test via web chat dengan pertanyaan Bahasa Indonesia!")
    print("3. Gunakan perintah /info atau /help untuk bantuan")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 