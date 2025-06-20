
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATION ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
LANGUAGE_ORDER = {
    "English": (0, 1),
    "Mandarin Chinese": (2, 3),
    "Hindi": (4, 5),
    "Spanish": (6, 7),
    "Arabic": (8, 9),
    "French": (10, 11),
    "Portuguese": (12, 13),
    "Swahili": (14, 15)
}

# --- LOAD UI TEXTS ---
with open("ui_text.json", "r", encoding="utf-8") as f:
    UI_TEXT = json.load(f)

# --- SESSION LANGUAGE SELECTOR ---
if "language" not in st.session_state:
    st.session_state.language = None

if st.session_state.language is None:
    st.title("🌍 Welcome!")
    st.markdown("Please select your language to begin:")
    selected = st.selectbox("🌐 Select language", list(LANGUAGE_ORDER.keys()))
    if selected:
        st.session_state.language = selected
        st.rerun()
    st.stop()

# --- INITIALIZATION ---
selected_language = st.session_state.language
term_idx, def_idx = LANGUAGE_ORDER[selected_language]
ui = UI_TEXT.get(selected_language, UI_TEXT["English"])

# --- PAGE SETTINGS ---
st.set_page_config(page_title="ToC Glossary", layout="wide")
st.title("📚 Theory of Change Glossary")
st.markdown("Explore translated terms related to the Theory of Change framework.")

# --- GOOGLE SHEETS AUTH ---
@st.cache_data(ttl=600)
def load_worksheet(sheet_name):
    return client.open_by_key(SHEET_ID).worksheet(sheet_name).get_all_values()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)

# --- LOAD RAW GLOSSARY DATA ---
data = load_worksheet("definitions")
data = data[1:]


# --- Extract terms/definitions by position ---
terms = [row[term_idx] for row in data if len(row) > def_idx and row[term_idx].strip()]
definitions = [row[def_idx] for row in data if len(row) > def_idx and row[term_idx].strip()]
glossary_df = pd.DataFrame({"Term": terms, "Definition": definitions})

# --- Dropdown Selector ---
selected_term = st.selectbox("🔍 Select a glossary term", [""] + glossary_df["Term"].tolist())

if selected_term:
    row = glossary_df[glossary_df["Term"] == selected_term]
    if not row.empty:
        st.markdown(f"**🔹 {row['Term'].values[0]}**")
        st.markdown(f"📄 *{row['Definition'].values[0]}*")
