
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
    "Mandarin Chinese": "变革理论（ToC）",
    "Hindi": "परिवर्तन का सिद्धांत (टीओसी)",
    "Spanish": "Teoría del cambio (TdC)",
    "Arabic": "نظرية التغيير",
    "French": "Théorie du changement (ToC)",
    "Portuguese": "Teoria da Mudança (TdM)",
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
st.markdown(f"🪴 **{ui['intro_text_2']}**")

# --- SHOW ToC DEFINITION using position ---
glossary_data = load_worksheet("definitions")[1:]


term_idx, def_idx = LANGUAGE_ORDER[selected_language]
target_term = TERM_LOOKUP.get(selected_language, "Theory of Change (ToC)").strip().lower()

for row in glossary_data:
    if len(row) > def_idx and row[term_idx].strip().lower() == target_term:
        # Green, leafy definition card
        st.markdown(
            f"""
            <div style='
                background: linear-gradient(90deg,#29522a 100%,#5fa66c 100%);
                border-radius: 1.3rem;
                box-shadow: 0 2px 14px #29522a17;
                padding: 1.3rem 1.5rem 1.2rem 1.5rem;
                margin-bottom: 1.1rem;
                margin-top: 0.5rem;
                display: flex;
                align-items: flex-start;
                gap: 1.1rem;
            '>
                <span style='font-size:2.3rem; line-height:1; margin-top:-0.5rem;'>🌱</span>
                <div>
                    <div style='font-size:1.3rem;font-weight:700;color:#fff;letter-spacing:.01em;margin-bottom:0.35rem;'>
                        {ui['toc_label']}
                    </div>
                    <div style='color:#e7ffe7;font-size:1.09rem;line-height:1.5;font-style:italic;'>
                        {row[def_idx]}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
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

# --- VISUAL SELECTOR ---
st.markdown(f"{ui.get('select_component', 'Select a component')}")
selected_component = st.selectbox(
    " ",  # This keeps the selectbox right under the label
    [""] + all_components,
    key="component_select",
)



# --- DISPLAY COMPONENTS BY STAGE ---
for (stage_id, stage_name), group in grouped:
    # Green stage header
    st.markdown(
        f"""
        <div style='background:linear-gradient(90deg,#29522a 60%,#5fa66c 100%);padding:0.8rem 1.3rem 0.5rem 1.3rem;border-radius:1.2rem 1.2rem 0.6rem 0.6rem; margin-bottom:0.17rem; margin-top:1.1rem; box-shadow: 0 1px 7px #29522a22;'>
            <span style='color:white;font-size:1.21rem;font-weight:700;letter-spacing:.01em;'>🌱 {int(stage_id)}. {stage_name}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
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

        # Use component as summary text (plain)
        with st.expander(f"{component}", expanded=False):
            # Show component name big at the top of the expander
            st.markdown(f"<span style='font-size:1.15rem;font-weight:600;color:#29522a'>{component}</span>", unsafe_allow_html=True)
            st.markdown(f"{ui['definition']}: {definition}", unsafe_allow_html=False)
            st.markdown(f"{ui['example']}: {example}", unsafe_allow_html=False)
            st.markdown(f"{ui['general_question']}: {general_question}", unsafe_allow_html=False)
            st.markdown(f"{ui['detailed_questions']}: {detailed_questions}", unsafe_allow_html=False)
            st.markdown(f"{ui['why_important']}: {why_important}", unsafe_allow_html=False)
            st.markdown(f"{ui['how_to_address']}: {how_to_address}", unsafe_allow_html=False)


with st.sidebar:
    st.markdown("<hr style='margin-top:0.5rem;margin-bottom:0.7rem;'>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:1.17rem;font-weight:700;color:#29522a;margin-bottom:0.25rem;'>📚 {ui.get('glossary_title', 'Theory of Change Glossary')}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<span style='color:#376942;font-size:0.97rem'>{ui.get('glossary_intro', 'Key terms used throughout this tool.')}</span>",
        unsafe_allow_html=True
    )

    # Si el idioma cambió, resetea la selección y recarga el glosario
    if "last_glossary_language" not in st.session_state or st.session_state.last_glossary_language != selected_language:
        st.session_state["glossary_select"] = ""
        st.session_state.last_glossary_language = selected_language
        st.rerun()

    # Usar los datos ya cargados
    term_idx, def_idx = LANGUAGE_ORDER[selected_language]
    glossary_terms = [row[term_idx] for row in glossary_data if len(row) > def_idx and row[term_idx].strip()]
    glossary_defs = [row[def_idx] for row in glossary_data if len(row) > def_idx and row[term_idx].strip()]
    glossary_df = pd.DataFrame({"Term": glossary_terms, "Definition": glossary_defs})

    selected_term = st.selectbox(
        ui.get("select_glossary_term", "🔍 Search or select a term"),
        [""] + glossary_df["Term"].tolist(),
        key="glossary_select"
    )

    if selected_term:
        row = glossary_df[glossary_df["Term"] == selected_term]
        if not row.empty:
            st.markdown(
                f"<span style='font-size:1.04rem;font-weight:600;color:#29522a'>🔹 {row['Term'].values[0]}</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<span style='font-size:0.99rem;line-height:1.55;color:#223'>{row['Definition'].values[0]}</span>",
                unsafe_allow_html=True
            )


    st.markdown("<hr style='margin-top:1rem;margin-bottom:0.5rem;'>", unsafe_allow_html=True)
    st.markdown("**Source:**", unsafe_allow_html=True)
    st.markdown(
        "[Pringle, P., & Thomas, A. (2019). *Climate Adaptation and Theory of Change: Making it work for you*. IMPACT, Climate Analytics.](https://climateanalytics.org/publications/climate-adaptation-and-theory-of-change-making-it-work-for-you)",
        unsafe_allow_html=True
    )


