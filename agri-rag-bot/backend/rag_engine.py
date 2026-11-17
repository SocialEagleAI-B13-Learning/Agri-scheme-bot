import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# 1. Load the FAISS vector database from the root folder
# (Note the path goes up one level to find 'faiss_index')
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "faiss_index"))

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"FAISS index not found at {DB_PATH}. Run 'ingest.py' first!")

print("Loading FAISS vector database into memory...")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)

# 2. Create a Retriever (pulls top 4 most relevant chunks)
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

# 3. Initialize the LLM (gpt-4o-mini is fast, smart, and cost-effective)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# 4. Define a strict Prompt Template enforcing PDF and Page Number citations
template = """You are an expert Agricultural Government Scheme Assistant. 
Answer the user's question accurately using ONLY the provided context below. 
For every fact, rule, or subsidy detail you mention, you MUST explicitly cite the source PDF filename and Page Number in brackets (e.g.,). 
If the answer is not present in the context, state clearly that the information is not available in the loaded government scheme documents.

Context:
{context}

User Question: {question}

Detailed Answer (with mandatory PDF and Page Number citations):"""

prompt = ChatPromptTemplate.from_template(template)

# Helper function to format retrieved documents and keep track of metadata
def format_docs(docs):
    formatted = []
    for doc in docs:
        source_file = os.path.basename(doc.metadata.get("source", "Unknown PDF"))
        page_num = doc.metadata.get("page", 0) + 1  # PyPDFLoader pages are 0-indexed, so add 1
        content = doc.page_content
        formatted.append(f"--- Document: {source_file} | Page: {page_num} ---\n{content}")
    return "\n\n".join(formatted)

# 5. Build the RAG Chain using modern LangChain Expression Language (LCEL)
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def ask_scheme_question(question: str):
    """Function called by FastAPI to get the answer and source citations."""
    print(f"\nProcessing query: '{question}'")
    
    # Retrieve docs separately so we can return structured citations if needed
    retrieved_docs = retriever.invoke(question)
    
    # Run the RAG chain
    response = rag_chain.invoke(question)
    
    # Collect unique sources for transparency
    sources = []
    for doc in retrieved_docs:
        src = os.path.basename(doc.metadata.get("source", "Unknown"))
        pg = doc.metadata.get("page", 0) + 1
        sources.append({"file": src, "page": pg})
        
    return {
        "answer": response,
        "sources": sources
    }

# Quick test if run directly
if __name__ == "__main__":
    test_query = "What are the eligibility criteria and subsidy details for agricultural machinery?"
    result = ask_scheme_question(test_query)
    print("\n--- ANSWER ---")
    print(result["answer"])
    print("\n--- SOURCES USED ---")
    print(result["sources"])