
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

TERM_LOOKUP = {
    "English": "Theory of Change (ToC)",
    "Mandarin Chinese": "变革理论 (ToC)",
    "Hindi": "परिवर्तन के सिद्धांत (ToC)",
    "Spanish": "Teoría del Cambio (ToC)",
    "Arabic": "نظرية التغيير (ToC)",
    "French": "Théorie du changement (ToC)",
    "Portuguese": "Teoria da Mudança (ToC)",
    "Swahili": "Nadharia ya Mabadiliko (ToC)"
}

# --- PAGE SETTINGS ---
st.set_page_config(page_title="ToC Explorer", layout="wide")

# --- Load UI text ---
with open("ui_text.json", "r", encoding="utf-8") as f:
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
        st.experimental_rerun()
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
st.title(ui["title"])
st.markdown(ui["intro"])
st.markdown(f"🪴 *{ui['intro_text_2']}*")

# --- SHOW ToC DEFINITION using position ---
glossary_data = load_worksheet("definitions")[1:]

term_idx, def_idx = LANGUAGE_ORDER[selected_language]

target_term = TERM_LOOKUP.get(selected_language, "Theory of Change (ToC)").strip().lower()
for row in glossary_data:
    if len(row) > def_idx and row[term_idx].strip().lower() == target_term:
        st.markdown(f"### {ui['toc_label']}")
        st.markdown(f"📄 *{row[def_idx]}*")
        break


# --- LOAD COMPONENTS DATA ---
component_ws = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
data = component_ws.get_all_values()
columns = data[0]
rows = data[1:]
df = pd.DataFrame(rows, columns=columns)

# --- Display by Stage ID ---
df["Stage_ID"] = df.iloc[:, 1]
df["Stage_Name"] = df.iloc[:, 2]
grouped = df.groupby(["Stage_ID", "Stage_Name"])
all_components = df.iloc[:, 3].dropna().unique().tolist()
selected_component = st.selectbox("🔍 Select a component", [""] + all_components)

for (stage_id, stage_name), group in grouped:
    st.subheader(f"📘 {int(stage_id)}. {stage_name}")
    for _, row in group.iterrows():
        component = row[3]
        if selected_component and component != selected_component:
            continue

        definition = row[4]
        example = row[5]
        general_question = row[6]
        detailed_questions = row[7]
        why_important = row[10]
        how_to_address = row[11]

        with st.expander(f"🔹 **{component}**", expanded=False):
            st.markdown(f"{ui['definition']}: {definition}")
            st.markdown(f"{ui['example']}: {example}")
            st.markdown(f"{ui['general_question']}: {general_question}")
            st.markdown(f"{ui['detailed_questions']}: {detailed_questions}")
            st.markdown(f"{ui['why_important']}: {why_important}")
            st.markdown(f"{ui['how_to_address']}: {how_to_address}")
