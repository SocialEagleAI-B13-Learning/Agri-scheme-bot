import streamlit as st
import requests

# FastAPI Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="வேளாண் வழிகாட்டி | Agri-Scheme Hub",
    page_icon="🌾",
    layout="wide"
)

# Custom Agri-Themed CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f9f4; }
    .main-header { font-size: 2.2rem; color: #1b5e20; font-weight: 800; margin-bottom: 0; }
    .sub-header { font-size: 1.05rem; color: #33691e; margin-top: 4px; }
    [data-testid="stSidebar"] { background-color: #e8f5e9; border-right: 1px solid #c8e6c9; }
    .fact-card {
        background-color: #ffffff;
        border: 1px solid #c8e6c9;
        border-left: 5px solid #2e7d32;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(27, 94, 32, 0.06);
    }
    .fact-title { color: #1b5e20; font-weight: 700; font-size: 1.1rem; margin-bottom: 6px; }
    .fact-body { color: #263238; font-size: 0.95rem; margin-bottom: 10px; }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #1b5e20; color: white; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


def query_backend(question: str):
    """Send question to FastAPI RAG backend and format answer + PDF page citations."""
    try:
        res = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=60)
        if res.status_code == 200:
            data = res.json()
            answer = data.get("answer", "No answer returned.")
            sources = data.get("sources", [])

            formatted = f"{answer}\n\n**📚 Source References:**"
            seen = set()
            for src in sources:
                key = (src.get("file"), src.get("page"))
                if key not in seen:
                    seen.add(key)
                    formatted += f"\n- `{key[0]}` (Page {key[1]})"
            return formatted
        err_msg = res.json().get("detail", "Server error occurred.")
        return f"⚠️ Error: {err_msg}"
    except Exception as e:
        return f"⚠️ Could not connect to FastAPI backend at `{BACKEND_URL}`. Ensure Uvicorn is running.\n\nDetails: {e}"


# --- Top Header + Pop-Up Chatbot Trigger ---
col_title, col_pop = st.columns([4, 1.3], vertical_alignment="center")

with col_title:
    st.markdown('<p class="main-header">🌾 வேளாண் வழிகாட்டி (Velaan Vazhikaatti) — Schemes Hub</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explore key scheme facts & official portals, or pop up the AI assistant in English, தமிழ், or Tanglish with exact PDF & page citations.</p>', unsafe_allow_html=True)

with col_pop:
    with st.popover("💬 Pop-Up AI Chatbot", use_container_width=True):
        st.markdown("### 🌱 உழவன் துணைவன்")
        st.caption("Supports English, தமிழ், & Tanglish • Includes PDF & page citations.")

        # Quick sample prompts in English, Tamil, and Tanglish
        st.markdown("**Quick Prompts:**")
        q_col1, q_col2, q_col3 = st.columns(3)
        with q_col1:
            if st.button("EN: Subsidy", key="prompt_en", use_container_width=True):
                st.session_state.pending_question = "What are the eligibility criteria and subsidy details for agricultural machinery?"
                st.rerun()
        with q_col2:
            if st.button("தமிழ்: தகுதி", key="prompt_ta", use_container_width=True):
                st.session_state.pending_question = "வேளாண் இயந்திர மானியத்திற்கான தகுதிகள் என்ன?"
                st.rerun()
        with q_col3:
            if st.button("Tanglish", key="prompt_tg", use_container_width=True):
                st.session_state.pending_question = "Agricultural machinery subsidy ku eligibility enna?"
                st.rerun()

        # If user clicked a quick question (from a card or quick prompt), run it
        if st.session_state.pending_question:
            q = st.session_state.pending_question
            st.session_state.pending_question = None
            st.session_state.messages.append({"role": "user", "content": q})
            with st.spinner("Searching scheme PDFs..."):
                reply = query_backend(q)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        # Chat history container inside pop-up
        chat_box = st.container(height=300)
        with chat_box:
            if not st.session_state.messages:
                st.info("Ask in English, தமிழ், or Tanglish below—or click a quick prompt above!")
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Input form inside pop-up
        with st.form(key="popup_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Type your question (English / தமிழ் / Tanglish)",
                placeholder="e.g., Machinery subsidy evalavu? / மானியம் எவ்வளவு?",max_chars=500
            )
            submitted = st.form_submit_button("Send 🚀", use_container_width=True)
            if submitted and user_input.strip():
                st.session_state.messages.append({"role": "user", "content": user_input.strip()})
                with st.spinner("Searching scheme PDFs..."):
                    reply = query_backend(user_input.strip())
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

st.markdown("---")

# --- Sidebar: PDF Upload & Knowledge Base ---
with st.sidebar:
    st.markdown("## 🚜 வேளாண் வழிகாட்டி")
    st.markdown("Upload new scheme PDFs to rebuild your FAISS index.")

    uploaded_file = st.file_uploader("Upload Scheme PDF", type=["pdf"])
    if uploaded_file is not None:
        if st.button("📤 Upload & Rebuild Index", use_container_width=True):
            with st.spinner("Uploading and updating FAISS vector database..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{BACKEND_URL}/upload-pdf", files=files, timeout=120)
                    if response.status_code == 200:
                        st.success(f"Added '{uploaded_file.name}' and rebuilt index!")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Main Screen: Important Facts & Clickable Portals ---
st.subheader("📌 Key Agricultural Scheme Highlights & Reference Portals")

highlights = [
    {
        "title": "🚜 Farm Mechanization & Machinery Subsidies",
        "fact": "Covers subsidy support and eligibility guidelines for purchasing agricultural machinery, implements, and custom hiring centers.",
        "url": "https://agritech.tnau.ac.in/agricultural_engineering/agriengg_govt_schemes.html",
        "link_label": "Open TNAU Agri-Engg Schemes Portal",
        "sample_q": "What are the eligibility criteria and subsidy details for agricultural machinery?"
    },
    {
        "title": "💧 Micro-Irrigation & Water Conservation",
        "fact": "Focuses on efficient water use, drip/sprinkler systems, and farm pond/water-harvesting guidelines in scheme documents.",
        "url": "https://pmksy.gov.in/",
        "link_label": "Open PMKSY Official Portal",
        "sample_q": "What are the guidelines and benefits for irrigation and water conservation schemes?"
    },
    {
        "title": "📋 Farmer Eligibility & Application Process",
        "fact": "Check required land/farmer documents, category norms, and approval steps specified across your uploaded scheme PDFs.",
        "url": "https://agritech.tnau.ac.in/",
        "link_label": "Open TNAU Agritech Portal",
        "sample_q": "What documents and eligibility rules apply to farmers applying for these schemes?"
    },
    {
        "title": "🌾 National Agriculture & Farmer Support",
        "fact": "Explore broader central agricultural scheme information and cross-check details against your local ingested PDFs.",
        "url": "https://agriwelfare.gov.in/",
        "link_label": "Open Dept. of Agriculture & Farmers Welfare",
        "sample_q": "Summarize the main schemes and key benefits listed in the uploaded PDFs."
    }
]

c1, c2 = st.columns(2)
for idx, item in enumerate(highlights):
    target_col = c1 if idx % 2 == 0 else c2
    with target_col:
        st.markdown(
            f"""
            <div class="fact-card">
                <div class="fact-title">{item["title"]}</div>
                <div class="fact-body">{item["fact"]}</div>
                <a href="{item["url"]}" target="_blank">🔗 {item["link_label"]}</a>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button(f"💬 Ask AI about: {item['title'].split(' ', 1)[1]}", key=f"btn_{idx}"):
            st.session_state.pending_question = item["sample_q"]
            st.toast("Question queued! Click '💬 Pop-Up AI Chatbot' at the top right to view the answer.", icon="🌾")