import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATION ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
LANGUAGE_COLS = {
    "English": 0,
    "Mandarin Chinese": 1,
    "Hindi": 2,
    "Spanish": 3,
    "Arabic": 4,
    "French": 5,
    "Portuguese": 6,
    "Swahili": 7
}
SOURCE_COL_INDEX = 8

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Recommendations Tool", layout="wide")

# --- Load UI text ---
with open("ui_text.json", "r", encoding="utf-8") as f:
    UI_TEXT = json.load(f)

with open("ui_recommendations.json", "r", encoding="utf-8") as f:
    UI_RECS = json.load(f)

# --- Session language selection ---
if "language" not in st.session_state:
    st.title("🌍 Welcome!")
    st.markdown("Please select your language to begin:")
    selected = st.selectbox("🌐 Select language", list(LANGUAGE_COLS.keys()))
    if selected:
        st.session_state.language = selected
        st.rerun()
    st.stop()

selected_language = st.session_state.language

# --- Load language-specific UI text ---
ui = UI_TEXT.get(selected_language, UI_TEXT["English"])
ui_rec = UI_RECS.get(selected_language, UI_RECS["English"])

# --- Allow language switch ---
with st.sidebar:
    st.markdown("🌐 **Change language**")
    new_lang = st.selectbox("Language", list(LANGUAGE_COLS.keys()), index=list(LANGUAGE_COLS.keys()).index(selected_language))
    if new_lang != selected_language:
        st.session_state.language = new_lang
        st.rerun()

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
st.markdown(f"<h1 style='color:#29522a;'>{ui_rec['section_title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.05rem; color:#3a3a3a; margin-bottom:1.2rem;'>{ui_rec['intro_text']}</div>", unsafe_allow_html=True)

# --- LOAD AND DISPLAY FLAT RECOMMENDATIONS ---
raw_data = load_worksheet("recomendations")
header = raw_data[1]  # Second row = column headers
rows = raw_data[2:]   # Start from third row

rec_col = LANGUAGE_COLS[selected_language]
sources_seen = set()
count = 0

for row in rows:
    if len(row) > max(rec_col, SOURCE_COL_INDEX):
        rec = row[rec_col].strip()
        source = row[SOURCE_COL_INDEX].strip()
        if rec:
            count += 1
            sources_seen.add(source)
            st.markdown(
                f"<div style='background:#f4fafd; padding:0.6rem 1rem; margin:0.6rem 0; border-left:4px solid #a5cbe1;'>"
                f"<strong style='color:#1c5d75;'>💡 {count}.</strong> {rec}",
                unsafe_allow_html=True
            )

# --- BIBLIOGRAPHY SECTION IN SIDEBAR ---
st.sidebar.markdown("<hr style='margin-top:1.5rem; margin-bottom:0.8rem;'>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<div style='font-size:1.1rem; font-weight:700; color:#2c4a55;'>📚 Sourcey</div>",
    unsafe_allow_html=True
)

# --- DYNAMIC SOURCES ---
# if sources_seen:
#     for src in sorted(sources_seen):
#         st.sidebar.markdown(f"- {src}")

# --- FIXED BIBLIOGRAPHIC REFERENCES ---
st.sidebar.markdown("- Pringle, P., & Thomas, A. (2019). *Climate Adaptation and Theory of Change: Making it work for you*. IMPACT, Climate Analytics. [Link](https://climateanalytics.org/publications/climate-adaptation-and-theory-of-change-making-it-work-for-you)")
# st.sidebar.markdown("- Meadows, D. (1994). *Down to Earth* [Video]. [YouTube](https://www.youtube.com/watch?v=bxowxs22jFk)")
# st.sidebar.markdown("- Meadows, D. (1994). *Envisioning a Sustainable World*. The Academy for Systems Change. [Paper](https://donellameadows.org/archives/envisioning-a-sustainable-world/)")