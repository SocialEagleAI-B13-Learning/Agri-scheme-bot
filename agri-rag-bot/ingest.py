import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 1. Load environment variables from .env
load_dotenv()

def build_vector_database():
    pdf_folder = "pdfs"
    all_documents = []

    if not os.path.exists(pdf_folder):
        print(f"Error: '{pdf_folder}/' folder not found!")
        return

    # 2. Load all PDFs from the pdfs/ folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF(s) to ingest...")

    for filename in pdf_files:
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"Reading: {filename}...")
        loader = PyPDFLoader(pdf_path)
        # PyPDFLoader automatically tracks 'source' (filename) and 'page' number
        documents = loader.load()
        all_documents.extend(documents)

    print(f"\nTotal raw pages loaded across all PDFs: {len(all_documents)}")

    # 3. Split documents into smart chunks
    # chunk_size=1000 characters ensures enough context per chunk
    # chunk_overlap=200 prevents cutting sentences or subsidy tables in half
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(all_documents)
    print(f"Total text chunks created: {len(chunks)}")

    # 4. Generate OpenAI Embeddings and Store in FAISS
    print("\nGenerating embeddings using OpenAI and building FAISS index...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # 5. Save locally to the faiss_index folder we created earlier
    vector_store.save_local("faiss_index")
    print("\nSUCCESS! FAISS vector database saved successfully to 'faiss_index/' folder. 🚀")

if __name__ == "__main__":
    build_vector_database()