"""
StrateGPT V3
Run: python -m streamlit run v3/app.py
"""
import os, sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# On Streamlit Cloud, secrets live in st.secrets rather than .env
for _k in ("ANTHROPIC_API_KEY", "SP_DOCS_BASE", "SP_AMB45_BASE"):
    if _k not in os.environ:
        try:
            os.environ[_k] = st.secrets[_k]
        except (KeyError, FileNotFoundError):
            pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="StrateGPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not st.session_state.get("authenticated"):
    st.title("StrateGPT")
    password = st.text_input("Enter password to continue", type="password")
    if st.button("Login"):
        try:
            correct = st.secrets["password"]
        except (KeyError, FileNotFoundError):
            correct = os.environ.get("APP_PASSWORD", "")
        if password == correct and correct:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []
for key in ("history_suggestions", "amb45_suggestions"):
    if key not in st.session_state:
        st.session_state[key] = None

chat_page      = st.Page("pages/chat.py",      title="Chat",               icon="💬", default=True)
explorer_page  = st.Page("pages/explorer.py",  title="Document Explorer",  icon="📁")
connector_page = st.Page("pages/connector.py", title="Strategy Connector", icon="🔀")

pg = st.navigation([chat_page, explorer_page, connector_page])
pg.run()
