
import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import random

# --- CONFIG ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
COMPONENT_SHEET_PREFIX = "components_"

# Column index constants
IDX_COMPONENT = 3
IDX_DEFINITION = 4

with open("game_text_minimal_multilang.json", "r", encoding="utf-8") as f:
    GAME_TEXT = json.load(f)

LANGUAGES = list(GAME_TEXT.keys())

LANGUAGE_CODES = {
    "English": "en",
    "Mandarin Chinese": "zh-CN",
    "Hindi": "hi",
    "Spanish": "es",
    "Arabic": "ar",
    "French": "fr",
    "Portuguese": "pt",
    "Swahili": "sw",
}

# --- SESSION STATE ---
for k, v in {
    "language": LANGUAGES[0],
    "name": "",
    "in_game": False,
    "current_q": 0,
    "correct_q": 0,
    "ascii_stage": 0,
    "answers": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- AUTH ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)

# --- UI ---
ui = GAME_TEXT[st.session_state.language]

st.set_page_config(page_title=ui["title"], layout="wide")
st.sidebar.selectbox("🌐 Language", LANGUAGES, index=LANGUAGES.index(st.session_state.language), key="language")
st.title(ui["title"])
st.markdown(ui["intro"])

# --- COMPONENT LOADER ---
@st.cache_data(ttl=1800)
def load_component_data(sheet_name):
    ws = client.open_by_key(SHEET_ID).worksheet(sheet_name)
    data = ws.get_all_values()
    col_names = data[1]
    rows = data[2:]
    return pd.DataFrame(rows, columns=col_names)

# --- MAIN ---
if not st.session_state["in_game"]:
    st.text_input(ui["name_prompt"], key="name")
    if st.button(ui["start_button"]):
        st.session_state["in_game"] = True
        st.session_state["current_q"] = 0
        st.session_state["correct_q"] = 0
        st.session_state["ascii_stage"] = 0
        st.session_state["answers"] = []
        st.rerun()

if st.session_state["in_game"]:
    lang_code = LANGUAGE_CODES.get(st.session_state.language, "en")
    sheet_name = COMPONENT_SHEET_PREFIX + lang_code
    df = load_component_data(sheet_name)
    df = df[df.iloc[:, IDX_COMPONENT].notna() & df.iloc[:, IDX_DEFINITION].notna()].reset_index(drop=True)

    n_questions = 6
    if "question_list" not in st.session_state:
        st.session_state.question_list = df.sample(n=n_questions)

    questions = st.session_state.question_list
    curr_idx = st.session_state.current_q

    if curr_idx < n_questions:
        row = questions.iloc[curr_idx]
        component = row.iloc[IDX_COMPONENT]
        correct_answer = row.iloc[IDX_DEFINITION]

        st.markdown(f"**{curr_idx + 1}. {component}**")
        st.markdown(f"{correct_answer}")

        pool = df.iloc[:, IDX_DEFINITION].dropna().unique().tolist()
        pool = [x for x in pool if x != correct_answer]
        options = random.sample(pool, 3) + [correct_answer]
        random.shuffle(options)

        selected = st.radio(ui["question_instruction"], options, key=f"q_{curr_idx}")
        if st.button(ui["next_question"], key=f"submit_{curr_idx}"):
            is_correct = selected == correct_answer
            st.session_state.answers.append({
                "question": correct_answer,
                "component": component,
                "your_answer": selected,
                "correct": is_correct,
            })
            if is_correct:
                st.session_state.correct_q += 1
                st.session_state.ascii_stage = min(st.session_state.ascii_stage + 1, 5)
                st.success(ui["correct_feedback"])
            else:
                st.session_state.ascii_stage = "dead"
                st.error(ui["fail_message"])
                st.session_state.in_game = False
                st.stop()
            st.session_state.current_q += 1
            st.rerun()

        stage = str(st.session_state.ascii_stage)
        st.markdown(f"<pre>{ui['ascii_stages'][stage]['art']}</pre>", unsafe_allow_html=True)
        st.markdown(ui['ascii_stages'][stage]['desc'])

    elif curr_idx == n_questions:
        st.success(ui["congrats"])
        st.markdown(ui["final_score"].format(score=st.session_state.correct_q))
        st.markdown(random.choice(ui["celebration_messages"]))
        if st.button(ui["play_again"]):
            st.session_state.in_game = False
            del st.session_state["question_list"]
            st.rerun()
