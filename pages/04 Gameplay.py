import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from io import BytesIO
import random



# --- CONFIGURATION ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
GAME_SHEET = "tomato_game_results"
COMPONENT_SHEET_PREFIX = "components_"
DIFFICULTY_MAP = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
    "extrahard": 3
}
DIFFICULTY_KEYS = list(DIFFICULTY_MAP.keys())

# --- LOAD UI TEXT ---
with open("game_text.json", "r", encoding="utf-8") as f:
    GAME_TEXT = json.load(f)

with open("ui_text.json", "r", encoding="utf-8") as f:
    UI_TEXT = json.load(f)

LANGUAGES = list(GAME_TEXT.keys())

# same as home.py
LANGUAGE_CODES = {
    "English":      "en",
    "Mandarin Chinese": "zh-CN",
    "Hindi":        "hi",
    "Spanish":      "es",
    "Arabic":       "ar",
    "French":       "fr",
    "Portuguese":   "pt",
    "Swahili":      "sw",
}


# --- SESSION LANGUAGE SELECTION ---
if "language" not in st.session_state:
    st.session_state.language = LANGUAGES[0]
if "name" not in st.session_state:
    st.session_state.name = ""
if "difficulty" not in st.session_state:
    st.session_state.difficulty = None
if "total_tomatoes" not in st.session_state:
    st.session_state.total_tomatoes = 0
if "harvest_history" not in st.session_state:
    st.session_state.harvest_history = []
if "unlocked_varieties" not in st.session_state:
    st.session_state.unlocked_varieties = set()

# --- PAGE LAYOUT ---
st.set_page_config(page_title=GAME_TEXT[st.session_state.language]["title"], layout="wide")


st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] .css-ng1t4o {
        padding-top: 3.5rem;  /* push space for header */
    }
    div[data-testid="stSidebarNav"]::before {
        content: "🌱 Theory of Change App";
        display: block;
        font-size: 1.3rem;
        font-weight: 700;
        color: #29522a;
        margin: 0 1.5rem 1rem 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


ui = GAME_TEXT[st.session_state.language]
plant_palette = {
    "easy": "#6ec47b",
    "medium": "#e1bb69",
    "hard": "#c7655b",
    "extrahard": "#548e68"
}

# --- AUTH ---
@st.cache_data(ttl=600)
def load_worksheet(sheet_name):
    return client.open_by_key(SHEET_ID).worksheet(sheet_name).get_all_values()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)



# --- LOAD COMPONENT DATA ---
@st.cache_data(ttl=1800)
def load_component_data(sheet_name):
    ws = client.open_by_key(SHEET_ID).worksheet(sheet_name)
    data = ws.get_all_values()
    # Row 1 (0-based) is your header row, row 2 is the column names
    col_names = data[1]
    rows = data[2:]
    df = pd.DataFrame(rows, columns=col_names)
    return df

# --- COLUMN INDEXES (ALWAYS BY POSITION) ---
IDX_ORDER = 0
IDX_STAGE_ID = 1
IDX_STAGE = 2
IDX_COMPONENT = 3
IDX_DEFINITION = 4
IDX_EXAMPLE = 5
IDX_GEN_GUIDING_Q = 6
IDX_DETAILED_GUIDING_Q = 7
IDX_DIAGNOSTIC_Q = 8
IDX_CLARIFY_PROMPT = 9
IDX_WHY_IMPORTANT = 10
IDX_HOW_TO_ADDRESS = 11




# --- LOAD LEADERBOARD ---
@st.cache_data(ttl=120)
def load_leaderboard():
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(GAME_SHEET)
        data = sheet.get_all_values()
        if len(data) < 2:
            return pd.DataFrame(columns=["Name", "Tomatoes", "League", "Variety", "Date & Time"])
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception:
        # Create worksheet if not exists
        sh = client.open_by_key(SHEET_ID)
        sh.add_worksheet(title=GAME_SHEET, rows=1000, cols=10)
        header = ["Name", "Tomatoes", "League", "Variety", "Date & Time"]
        sh.worksheet(GAME_SHEET).append_row(header)
        return pd.DataFrame(columns=header)

def append_leaderboard_row(name, tomatoes, league, variety, dt):
    sheet = client.open_by_key(SHEET_ID).worksheet(GAME_SHEET)
    sheet.append_row([name, str(tomatoes), league, variety, dt])

# --- LANGUAGE SWITCHER ---
with st.sidebar:
    st.markdown("🌐 **Change language**")
    lang = st.selectbox("Language", LANGUAGES, index=LANGUAGES.index(st.session_state.language))
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.rerun()

    # Leaderboard refresh button
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

    # --- LEADERBOARD SIDEBAR ---
    st.markdown(
        f"<div style='font-size:1.18rem;font-weight:700;color:#c7655b;margin:0.9rem 0 0.12rem 0;'>🍅 {ui['leaderboard_title']}</div>",
        unsafe_allow_html=True
    )
    lb = load_leaderboard()
    for key in DIFFICULTY_KEYS:
        league_label = ui.get(key, key.title())
        st.markdown(
            f"<div style='background:{plant_palette[key]};color:#fff;font-weight:600;border-radius:0.8rem 0.8rem 0.6rem 0.6rem;padding:0.23rem 0.8rem 0.12rem 0.8rem;font-size:1.02rem;margin-top:0.2rem;margin-bottom:0.13rem'>{ui['top_players_league'].format(league=league_label)}</div>",
            unsafe_allow_html=True
        )
        subdf = lb[lb["League"] == league_label].sort_values(by="Tomatoes", ascending=False).head(5)
        for i, row in subdf.iterrows():
            st.markdown(
                f"<div style='font-size:0.95rem;color:#29522a;background:rgba(255,255,255,0.85);margin-bottom:-0.11rem;'><b>{row['Name']}</b> — {row['Tomatoes']} 🍅 <span style='color:#8b7000'>[{row['Variety']}]</span> <br><span style='font-size:0.85rem;color:#666'>{row['Date & Time']}</span></div>",
                unsafe_allow_html=True
            )

    if st.button(ui.get("see_top_50", "See Top 50")):
        st.session_state.show_top_50 = True
    if st.session_state.get("show_top_50", False):
        st.markdown(f"### {ui['leaderboard_title']} (Top 50)")
        st.dataframe(lb.sort_values(by="Tomatoes", ascending=False).head(50), use_container_width=True)
        if st.button(ui.get("back_to_top_5", "Back to Top 5")):
            st.session_state.show_top_50 = False

# --- MAIN AREA ---
st.title(ui["title"])
st.markdown(f"<div style='font-size:1.12rem;color:#29522a;margin-bottom:0.5rem'>{ui['intro']}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='color:#376942;font-size:0.98rem;margin-bottom:0.7rem'>{ui['narrative_intro']}</div>", unsafe_allow_html=True)


# --- NAME AND DIFFICULTY SELECTION ---
if "in_game" not in st.session_state or not st.session_state["in_game"]:
    with st.form("start_form"):
        difficulty_options = [ui["easy"], ui["medium"], ui["hard"], ui["extrahard"]]
        default_index = (
            difficulty_options.index(st.session_state.difficulty)
            if st.session_state.get("difficulty") in difficulty_options
            else 0
        )
        # User input fields (Streamlit manages .name and .difficulty)
        st.text_input(ui["name_prompt"], value=st.session_state.name, key="name")
        st.selectbox(
            ui["difficulty_select"],
            difficulty_options,
            index=default_index,
            key="difficulty"
        )
        difficulty_key = DIFFICULTY_KEYS[default_index]
        st.markdown(
            f"<div style='color:#548e68;font-size:0.99rem;margin-bottom:0.35rem'>{ui['explanation_' + difficulty_key]}</div>",
            unsafe_allow_html=True
        )
        submitted = st.form_submit_button(ui["start_button"])
        if submitted:
            # Use a new key for processed name (do NOT assign to .name!)
            st.session_state["name_for_game"] = (
                st.session_state.name.strip() or ui.get("name_default", "Tomato Farmer")
            )
            st.session_state["in_game"] = True
            st.session_state["current_q"] = 0
            st.session_state["correct_q"] = 0
            st.session_state["ascii_stage"] = 0
            st.session_state["answers"] = []
            st.rerun()


# --- GAME LOGIC ---
if st.session_state.get("in_game", False):
    # Map the selected difficulty label back to the internal key
    difficulty_options = [ui["easy"], ui["medium"], ui["hard"], ui["extrahard"]]
    difficulty_label = st.session_state.difficulty  # e.g., "Easy League (Cherry Tomato)"
    if difficulty_label in difficulty_options:
        league_key = DIFFICULTY_KEYS[difficulty_options.index(difficulty_label)]
    else:
        league_key = "easy"  # fallback
    league_label = ui[league_key]
    variety = ui["varieties"][league_key]
    lang = st.session_state.language
    lang_code = LANGUAGE_CODES.get(lang, "en")
    comp_sheet = COMPONENT_SHEET_PREFIX + lang_code

    
    df = load_component_data(comp_sheet)

    # drop rows missing any of the core fields (using our positional IDX_ constants)
    cols = df.columns.tolist()
    required = [
        cols[IDX_COMPONENT],
        cols[IDX_DEFINITION],
        cols[IDX_EXAMPLE],
        cols[IDX_GEN_GUIDING_Q],
    ]
    df = df.dropna(axis=0, subset=required).reset_index(drop=True)



    # Question type logic
    if league_key == "easy":
        col_idx = IDX_DEFINITION
    elif league_key == "medium":
        col_idx = IDX_EXAMPLE
    elif league_key == "hard":
        col_idx = IDX_GEN_GUIDING_Q
    else:
        col_idx, _ = random.choice([
            (IDX_DEFINITION, "definition"),
            (IDX_EXAMPLE, "example"),
            (IDX_GEN_GUIDING_Q, "general")
        ])
    n_questions = 6

    # Get list of random components/questions for this round
    if "question_list" not in st.session_state or st.session_state.get("round_id", None) != (st.session_state.difficulty, st.session_state.language):
        questions = df.sample(n=n_questions, replace=False)
        st.session_state.question_list = questions
        st.session_state.round_id = (st.session_state.difficulty, st.session_state.language)
        st.session_state.current_q = 0
        st.session_state.correct_q = 0
        st.session_state.answers = []
        st.session_state["ascii_stage"] = 0

    questions = st.session_state.question_list
    curr_idx = st.session_state.current_q
    correct_q = st.session_state.correct_q

    
    # --- Ask the question (positional version) ---
    cols     = df.columns.tolist()
    comp_col = cols[IDX_COMPONENT]
    def_col  = cols[IDX_DEFINITION]
    ex_col   = cols[IDX_EXAMPLE]
    gen_col  = cols[IDX_GEN_GUIDING_Q]
    
    if curr_idx < n_questions:
        qrow = st.session_state.question_list.iloc[curr_idx]

        # 1) Component label
        comp = qrow[comp_col]

        # 2) Choose which field to quiz
        if league_key == "easy":
            prompt_col = def_col
        elif league_key == "medium":
            prompt_col = ex_col
        elif league_key == "hard":
            prompt_col = gen_col
        else:
            prompt_col = random.choice([def_col, ex_col, gen_col])

        prompt = qrow[prompt_col]

        # 3) Render question
        st.markdown(
            f"<div style='font-size:1.12rem;font-weight:600;color:#29522a;margin-bottom:0.15rem'>"
            f"{curr_idx+1}. {comp}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-size:1.06rem;color:#112E4D;margin-bottom:0.12rem'>{prompt}</div>",
            unsafe_allow_html=True
        )
        

        # make sure you set this once when you build your questions:
        st.session_state.round_id = (st.session_state.difficulty, st.session_state.language)

        # then when you cache options:

        opt_key = f"options_{st.session_state.round_id[0]}_{st.session_state.round_id[1]}_{curr_idx}"
        if opt_key not in st.session_state:
            pool = df[prompt_col].dropna().unique().tolist()
            pool = [x for x in pool if x != prompt]
            distractors = random.sample(pool, 3)
            options = distractors + [prompt]
            random.shuffle(options)
            st.session_state[opt_key] = options

        options = st.session_state[opt_key]

     

        # 5) Let them choose
        selected = st.radio(
            ui["question_instruction"],
            options,
            key=f"sel_{curr_idx}"
        )
        
        for k, default in [
            ("in_game", False),
            ("current_q", 0),
            ("correct_q", 0),
            ("ascii_stage", 0),
            ("harvest_loss", False),
            ("just_failed", False),
        ]:
            if k not in st.session_state:
                st.session_state[k] = default


        # 6) On submit
        if st.button(ui.get("next_question", "Next Question"), key=f"submit_{curr_idx}"):
            correct = (selected == prompt)
            st.session_state.answers.append({
                "question": prompt,
                "component": comp,
                "your_answer": selected,
                "correct": correct,
                "correct_answer": prompt
            })

            if correct:
                st.session_state.correct_q += 1
                st.session_state["ascii_stage"] = min(st.session_state["ascii_stage"] + 1, 5)
                st.success(ui["correct_feedback"])
            else:
                st.session_state["ascii_stage"] = "dead"
                st.error(ui["fail_message"])
                st.session_state["in_game"]      = False
                st.session_state["harvest_loss"] = True
                st.session_state["just_failed"]  = True
                st.stop()

            st.session_state.current_q += 1
            st.rerun()
            
        
        # Show ASCII art stage
    st.markdown(
        f"<pre style='background: #e6f2e6; color:#29522a; font-size:1.2rem; border-radius:1rem; margin:0.6rem 0; padding:1.2rem 1rem;'>{ui['ascii_stages'][str(st.session_state['ascii_stage'])]['art']}</pre>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='font-size:1.02rem;color:#548e68; margin-bottom:0.23rem'>{ui['ascii_stages'][str(st.session_state['ascii_stage'])]['desc']}</div>",
        unsafe_allow_html=True
    )


                

     # 7) Once they’ve answered all n_questions correctly in a row
    if st.session_state.current_q == n_questions and not st.session_state.harvest_loss:
        # unlock the new variety
        st.session_state.unlocked_varieties.add(variety)

        # congratulations header
        st.markdown(
            f"<div style='font-size:1.23rem;font-weight:700;"
            f"color:{plant_palette[league_key]};margin-bottom:0.2rem'>"
            f"{ui['congrats']}</div>",
            unsafe_allow_html=True
        )

    
        # summary of this round
        last = st.session_state.correct_q
        st.markdown(
            f"<div style='font-size:1.08rem;color:#548e68;'>"
            f"{ui['final_score'].format(score=last)}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:#112E4D;'>"
            f"{ui['your_variety'].format(variety=variety)}<br>"
            f"{ui['your_league'].format(league=league_label)}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:#c7655b;font-size:1.05rem;margin-top:0.12rem'>"
            f"{ui['your_harvest'].format(total=st.session_state.total_tomatoes)}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:#29522a;font-size:0.98rem'>"
            f"{random.choice(ui['celebration_messages'])}</div>",
            unsafe_allow_html=True
        )

        # # list all unlocked varieties
        # unlocked = ", ".join(st.session_state.unlocked_varieties)
        # st.markdown(
        #     f"<span style='color:#376942;font-size:0.98rem'>"
        #     f"{ui['grown_varieties'].format(varieties=unlocked)}</span>",
        #     unsafe_allow_html=True
        # )
        
          # Play Again / Reset
          
        if st.button(ui["play_again"]):
                # reset round state
                st.session_state.in_game      = True
                st.session_state.current_q    = 0
                st.session_state.correct_q    = 0
                st.session_state.ascii_stage  = 0
                st.session_state.answers      = []

                # completely remove old questions + round tracking
                for k in ("question_list", "round_id"):
                    if k in st.session_state:
                        del st.session_state[k]

                # clear out any leftover options_* caches
                for key in list(st.session_state.keys()):
                    if key.startswith("options_"):
                        del st.session_state[key]

                st.rerun()
    col1, col2 = st.columns([1, 1])
    with col1:
            if st.button(ui["play_again"]):
                # reset round state
                st.session_state.in_game      = True
                st.session_state.current_q    = 0
                st.session_state.correct_q    = 0
                st.session_state.ascii_stage  = 0
                st.session_state.answers      = []

                # completely remove old questions + round tracking
                for k in ("question_list", "round_id"):
                    if k in st.session_state:
                        del st.session_state[k]

                # clear out any leftover options_* caches
                for key in list(st.session_state.keys()):
                    if key.startswith("options_"):
                        del st.session_state[key]

                st.rerun()

    with col2:
        if st.button(ui.get("reset_button", "Reset My Name and Harvest")):
            st.session_state.name = ""
            st.session_state.total_tomatoes = 0
            st.session_state.harvest_history = []
            st.session_state.unlocked_varieties = set()
            st.session_state["in_game"] = False
            st.session_state["current_q"] = 0
            st.session_state["correct_q"] = 0
            st.session_state["ascii_stage"] = 0
            st.session_state["answers"] = []
            st.session_state["question_list"] = None
            st.session_state["harvest_loss"] = False
            st.session_state["just_failed"] = False
            st.rerun()

        
        
    #     can_publish = st.session_state.name and st.session_state.name != ui.get("name_default", "Tomato Farmer")
    #     if st.button(ui.get("publish_results", "Publish My Harvest to Leaderboard")):
    #         if can_publish:
    #             append_leaderboard_row(
    #                 st.session_state.name,
    #                 total,
    #                 league_label,
    #                 variety,
    #                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #             )
    #             st.success("Your result has been published to the leaderboard!")
    #             st.cache_data.clear()
    #             st.rerun()
    #         else:
    #             st.warning(ui.get("anonymous_warning", "You must enter your name to publish your harvest to the leaderboard."))


    #         # Download results
    #         hist_df = pd.DataFrame(st.session_state.harvest_history)
    #         if not hist_df.empty:
    #             excel_buffer = BytesIO()
    #             hist_df.to_excel(excel_buffer, index=False)
    #             st.download_button(
    #                 ui.get("download_results", "Download My Harvest as Excel"),
    #                 data=excel_buffer.getvalue(),
    #                 file_name="my_tomato_harvest.xlsx",
    #                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #             )
    #             st.markdown(f"<span style='color:#8b7000;font-size:0.92rem'>{ui['download_history_hint']}</span>", unsafe_allow_html=True)

   
  




# --- GAME OVER (FAILURE) ---
if st.session_state.get("harvest_loss", False) and st.session_state.get("just_failed", False):
    st.markdown(
        f"<pre style='background: #ffecec; color:#a43838; font-size:1.1rem; border-radius:1rem; margin:0.7rem 0; padding:1.2rem 1rem;'>{ui['ascii_dead']['art']}</pre>",
        unsafe_allow_html=True
    )
    st.markdown(f"<div style='color:#a43838;font-size:1.06rem;margin-bottom:0.19rem'>{ui['ascii_dead']['desc']}</div>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#29522a;font-size:0.97rem'>{ui['dead_plant_message']}</span>", unsafe_allow_html=True)
    # User loses last harvest (but cannot go negative)
    if st.session_state.harvest_history:
        st.session_state.harvest_history = st.session_state.harvest_history[:-1]
        st.session_state.total_tomatoes = max(0, st.session_state.total_tomatoes - 6)
    st.session_state["just_failed"] = False
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(ui.get("play_again", "Play Again"), key="fail_play_again"):
            st.session_state["in_game"] = True
            st.session_state["current_q"] = 0
            st.session_state["correct_q"] = 0
            st.session_state["ascii_stage"] = 0
            st.session_state["answers"] = []
            st.session_state["question_list"] = None
            st.session_state["harvest_loss"] = False
            st.rerun()
    with col2:
        if st.button(ui.get("stop_and_publish", "Stop & Publish")):
            st.session_state["harvest_loss"] = False
            st.rerun()


# from contact_me import render_footer

# # at the very end of the page
# render_footer(language=selected_language)