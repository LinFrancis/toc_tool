
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATION ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
LANGUAGE_SHEETS = {
    "English": "components_en",
    "Mandarin Chinese": "components_zh-CN",
    "Hindi": "components_hi",
    "Spanish": "components_es",
    "Arabic": "components_ar",
    "French": "components_fr",
    "Portuguese": "components_pt",
    "Swahili": "components_sw"
}

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


# --- PAGE SETTINGS ---
st.set_page_config(page_title="ToC Explorer", layout="wide")

# --- Load UI text ---
with open("ui_text_vision.json", "r", encoding="utf-8") as f:
    UI_TEXT = json.load(f)

# --- Session language ---
if "language" not in st.session_state:
    st.session_state.language = None

if st.session_state.language is None:
    st.title("🌍 Welcome!")
    st.markdown("Please select your language to begin:")
    selected = st.selectbox("🌐 Select language", list(LANGUAGE_SHEETS.keys()))
    if selected:
        st.session_state.language = selected
        st.rerun()
    st.stop()

selected_language = st.session_state.language
worksheet_name = LANGUAGE_SHEETS[selected_language]
ui = UI_TEXT.get(selected_language, UI_TEXT["English"])

# --- Allow language switch ---
with st.sidebar:
    st.markdown("🌐 **Change language**")
    new_lang = st.selectbox("Language", list(LANGUAGE_SHEETS.keys()), index=list(LANGUAGE_SHEETS.keys()).index(selected_language))
    if new_lang != selected_language:
        st.session_state.language = new_lang
        st.rerun()
        
     # --- Additional Sources ---
    st.markdown("<hr style='margin-top:1rem;margin-bottom:0.7rem;'>", unsafe_allow_html=True)
    st.markdown("**Sources:**", unsafe_allow_html=True)

    st.markdown(
        "[1. Donella Meadows – *Down to Earth* (1994), Video Recording](https://www.youtube.com/watch?v=bxowxs22jFk)",
        unsafe_allow_html=True
    )
    st.markdown(
        "[2. Donella Meadows – *Envisioning a Sustainable World* (1994), Paper](https://donellameadows.org/archives/envisioning-a-sustainable-world/)",
        unsafe_allow_html=True
    )

# --- AUTH ---

@st.cache_data(ttl=600)
def load_worksheet(sheet_name):
    return client.open_by_key(SHEET_ID).worksheet(sheet_name).get_all_values()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)



# --- TITLE AND INTRO ---
st.markdown(f"<h1 style='color:#29522a;'>{ui['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.05rem; color:#3a3a3a; margin-bottom:1rem;'>{ui['intro']}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.1rem; color:#548e68; font-weight:bold;'>🪴 {ui['intro_text_2']}</div>", unsafe_allow_html=True)

# --- LOAD and DISPLAY Envisioning Questions based on language ---
raw_data = load_worksheet("guiding_visions")
header = raw_data[1]  # Segunda fila: encabezados reales
rows = raw_data[2:]   # A partir de tercera fila: contenido

# Obtener índices de columnas correspondientes al idioma seleccionado
subtitle_col, question_col = LANGUAGE_ORDER[selected_language]

# Agrupar preguntas por subtítulo
grouped_questions = {}
for row in rows:
    if len(row) > max(subtitle_col, question_col):
        subtitle = row[subtitle_col].strip()
        question = row[question_col].strip()
        if subtitle and question:
            grouped_questions.setdefault(subtitle, []).append(question)

# Mostrar preguntas organizadas por subtítulo con estilo
for subtitle, questions in grouped_questions.items():
    st.markdown(
        f"<div style='background:#e6f2e6; padding:0.8rem 1rem; border-radius:0.6rem; margin:1.2rem 0 0.5rem;'>"
        f"<span style='font-size:1.2rem; font-weight:600; color:#29522a;'>🌀 {subtitle}</span>"
        f"</div>", 
        unsafe_allow_html=True
    )
    for i, q in enumerate(questions, start=1):
        st.markdown(
            f"<div style='background:#f8fbf8; padding:0.6rem 1rem; margin:0.3rem 0; border-left:4px solid #c7e0c7;'>"
            f"<strong style='color:#37623d;'>{i}.</strong> {q}"
            f"</div>",
            unsafe_allow_html=True
        )