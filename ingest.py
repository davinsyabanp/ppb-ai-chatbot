import os
import pandas as pd
from langchain_community.document_loaders import PyMuPDFLoader
from app.vector_store import create_vector_store
from app.langchain_compat import Document, RecursiveCharacterTextSplitter

def load_csv_file(file_path):
    """
    Load a CSV file and convert it to documents.
    Handles CSV files with quoted outer strings.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        list: List of Document objects
    """
    try:
        import csv
        from io import StringIO
        
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print(f"CSV file {file_path} is empty")
            return []
        
        # Extract and unquote headers from first line
        header_line = lines[0].strip()
        # Remove outer quotes if present
        if header_line.startswith('"') and header_line.endswith('"'):
            header_line = header_line[1:-1]
        headers = [h.strip() for h in header_line.split(',')]
        print(f"  Headers detected: {headers}")
        
        # Process data rows (skip header)
        for row_num, line in enumerate(lines[1:], start=2):
            line = line.strip()
            if not line:
                continue
            
            # Remove outer quotes if present
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            
            # Parse CSV line respecting quotes
            try:
                reader = csv.reader(StringIO(line))
                values = next(reader)
            except:
                # Fallback: simple split
                values = line.split(',')
            
            # Map headers to values
            row_text = ""
            for i, header in enumerate(headers):
                if i < len(values):
                    value = values[i].strip().strip('"')  # Remove quotes
                    if value:
                        row_text += f"{header}: {value}\n"
            
            if row_text.strip():
                metadata = {
                    "source": os.path.basename(file_path),
                    "row": row_num,
                    "file_type": "csv"
                }
                
                documents.append(Document(
                    page_content=row_text.strip(),
                    metadata=metadata
                ))
        
        print(f"Loaded CSV: {os.path.basename(file_path)} ({len(documents)} rows)")
        return documents
        
    except Exception as e:
        print(f"Error loading CSV file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return []

def load_pdf_file(file_path):
    try:
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        print(f"Loaded PDF: {os.path.basename(file_path)} ({len(docs)} pages)")
        return docs
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return []

def load_txt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            return [Document(page_content=text, metadata={"source": os.path.basename(file_path), "file_type": "txt"})]
    except Exception as e:
        print(f"Error loading TXT file {file_path}: {e}")
        return []

def load_documents():
    """
    Load documents from the documents folder.
    
    Returns:
        list: List of loaded documents
    """
    documents = []
    documents_dir = "documents"
    
    if not os.path.exists(documents_dir):
        print(f"Documents directory '{documents_dir}' not found. Creating it...")
        os.makedirs(documents_dir, exist_ok=True)
        print(f"Please add your documents (PDF, TXT, CSV) to the '{documents_dir}' folder and run this script again.")
        return documents
    
    # Get all files in the documents directory
    files = [f for f in os.listdir(documents_dir) if f.endswith(('.pdf', '.txt', '.csv'))]
    
    if not files:
        print(f"No documents found in '{documents_dir}' folder.")
        print("Please add your documents (PDF, TXT, CSV) to the documents folder and run this script again.")
        return documents
    
    print(f"Found {len(files)} document(s): {files}")
    
    # Load files based on their type
    for file in files:
        file_path = os.path.join(documents_dir, file)
        try:
            if file.endswith('.pdf'):
                docs = load_pdf_file(file_path)
                for d in docs:
                    d.metadata["file_type"] = "pdf"
                documents.extend(docs)
            elif file.endswith('.txt'):
                docs = load_txt_file(file_path)
                documents.extend(docs)
            elif file.endswith('.csv'):
                docs = load_csv_file(file_path)
                documents.extend(docs)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return documents

def split_documents_by_type(documents):
    csv_docs = [doc for doc in documents if doc.metadata.get("file_type") == "csv"]
    pdf_docs = [doc for doc in documents if doc.metadata.get("file_type") == "pdf"]
    txt_docs = [doc for doc in documents if doc.metadata.get("file_type") == "txt"]
    chunks = []
    # CSV chunking
    if csv_docs:
        csv_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks.extend(csv_splitter.split_documents(csv_docs))
    # PDF chunking
    if pdf_docs:
        pdf_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=400,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks.extend(pdf_splitter.split_documents(pdf_docs))
    # TXT chunking (use PDF settings for now)
    if txt_docs:
        txt_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=400,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks.extend(txt_splitter.split_documents(txt_docs))
    print(f"Split {len(documents)} documents into {len(chunks)} chunks")
    return chunks

def main():
    """
    Main function to process documents and create vector store.
    """
    print("Starting document ingestion process...")
    
    # Load documents
    documents = load_documents()
    if not documents:
        # If no documents, delete the vector DB directory if it exists
        import shutil
        vector_db_path = os.path.join("vector_db", "faiss_index")
        if os.path.exists(vector_db_path):
            print("No documents found. Deleting vector DB...")
            shutil.rmtree(vector_db_path)
            print("Vector DB deleted.")
        else:
            print("No documents and no vector DB to delete.")
        return
    
    # Split documents into chunks
    chunks = split_documents_by_type(documents)
    
    # Create vector store
    print("Creating vector store...")
    create_vector_store(chunks)
    
    print("Vector store created successfully!")

if __name__ == "__main__":
    main() 