import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print("--- STEP 1 VERIFICATION ---")
print("API Key Loaded:", "YES ✅" if api_key else "NO ❌ (Check your .env file)")

# Check PDFs folder
pdf_folder = "pdfs"
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

print(f"Found {len(pdf_files)} PDF(s) in '{pdf_folder}/':")
for pdf in pdf_files:
    loader = PyPDFLoader(os.path.join(pdf_folder, pdf))
    pages = loader.load()
    print(f" - {pdf}: {len(pages)} pages loaded successfully.")