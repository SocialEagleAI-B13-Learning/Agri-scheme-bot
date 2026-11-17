import streamlit as st
import requests

# FastAPI Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Agri-Scheme AI Assistant",
    page_icon="🌾",
    layout="wide"
)

# Custom Agri-Themed CSS Styling
st.markdown("""
    <style>
    .stApp { background-color: #f4f9f4; }
    .main-header { font-size: 2.3rem; color: #1b5e20; font-weight: 800; }
    .sub-header { font-size: 1.1rem; color: #33691e; margin-bottom: 15px; }
    [data-testid="stSidebar"] { background-color: #e8f5e9; border-right: 1px solid #c8e6c9; }
    .stButton>button { background-color: #2e7d32; color: white; border-radius: 6px; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #1b5e20; color: white; }
    </style>
""", unsafe_allow_html=True)

# App Title & Branding
st.markdown('<p class="main-header">🌾 Krishi-Sahayak: Agricultural Schemes AI Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your intelligent companion for government agricultural schemes, subsidies, and machinery guidelines with exact PDF & Page citations.</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for Knowledge Base Management
with st.sidebar:
    st.markdown("## 🚜 Knowledge Base")
    st.markdown("Upload official government scheme PDFs to expand the AI's database.")
    
    uploaded_file = st.file_uploader("Upload Scheme PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Upload & Rebuild Index"):
            with st.spinner("Processing PDF and updating FAISS vector database..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{BACKEND_URL}/upload-pdf", files=files)
                    if response.status_code == 200:
                        st.success(f"Successfully added '{uploaded_file.name}'!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    st.markdown("---")
    st.markdown("### 💡 Sample Questions to Try:")
    st.markdown("- What are the subsidy details for agricultural machinery?")
    st.markdown("- What is the eligibility criteria for farmers?")
    st.markdown("- Explain the application process for irrigation schemes.")

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if user_query := st.chat_input("Ask a question about government agricultural schemes..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("🌱 Searching government scheme documents..."):
            try:
                res = requests.post(f"{BACKEND_URL}/ask", json={"question": user_query})
                if res.status_code == 200:
                    data = res.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    
                    full_response = f"{answer}\n\n**📚 Source References:**"
                    for src in sources:
                        full_response += f"\n- `{src['file']}` (Page {src['page']})"
                        
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    err_msg = res.json().get("detail", "Server error occurred.")
                    st.error(f"Error: {err_msg}")
            except Exception as e:
                st.error(f"Could not connect to FastAPI backend at {BACKEND_URL}. Is Uvicorn running? Details: {e}")