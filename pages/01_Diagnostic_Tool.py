import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

# --- CONFIGURATION ---
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
LANGUAGE_CODES = {
    "English": "en",
    "Mandarin Chinese": "zh-CN",
    "Hindi": "hi",
    "Spanish": "es",
    "Arabic": "ar",
    "French": "fr",
    "Portuguese": "pt",
    "Swahili": "sw"
}

st.set_page_config(page_title="📋 Theory of Change Diagnostic Quiz", layout="wide")

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


# --- LOAD UI TEXT ---
with open("ui_text.json", "r", encoding="utf-8") as f:
    UI_TEXT = json.load(f)

# --- LANGUAGE SESSION ---
if "language" not in st.session_state:
    st.session_state.language = None

if st.session_state.language is None:
    st.title("🌍 Welcome!")
    st.markdown("Please select your language to begin:")
    selected = st.selectbox("🌐 Select language", list(LANGUAGE_CODES.keys()))
    if selected:
        st.session_state.language = selected
        st.rerun()
    st.stop()

selected_language = st.session_state.language
ui = UI_TEXT.get(selected_language, UI_TEXT["English"])
lang_code = LANGUAGE_CODES[selected_language]
sheet_name = f"components_{lang_code}"

# --- SIDEBAR LANGUAGE SWITCH ---
with st.sidebar:
    st.markdown("🌐 **Change language**")
    new_lang = st.selectbox("Language", list(LANGUAGE_CODES.keys()), index=list(LANGUAGE_CODES.keys()).index(selected_language))
    if new_lang != selected_language:
        st.session_state.language = new_lang
        st.rerun()

# --- GOOGLE SHEETS AUTH ---
@st.cache_data(ttl=600)
def load_worksheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(SHEET_ID).worksheet(sheet_name).get_all_values()

# --- LOAD DATA ---
data = load_worksheet(sheet_name)
rows = data[1:]  # Skip header

# Filter rows with diagnostic question (column 8)
df = pd.DataFrame([row for row in rows if len(row) >
                   8 and row[8].strip() != ""])

# Make sure Order is string, remove spaces, filter only rows with numbers
df[0] = df[0].astype(str).str.strip()
df = df[df[0].str.match(r"^\d+$")].copy()


# Get unique criteria by Stage (column 2)
criterion_order = pd.Series([row[2] for row in rows if len(row) > 2 and row[2].strip() != ""]).drop_duplicates().tolist()

# --- Instructions and Reference ---
st.title(ui.get("diagnostic_title", "Theory of Change Diagnostic Quiz"))
st.markdown(ui.get("diagnostic_intro_main", ""))
st.markdown(ui.get("diagnostic_intro_ref", ""))
st.markdown("---")

initiative_name = st.text_input(ui.get("initiative_name", "Initiative name"), placeholder=ui.get("initiative_name", ""))
show_summary_only = st.checkbox(ui.get("show_summary_only", "Show only the summary (hide detailed feedback)"))

responses = {}

with st.form("grouped_quiz_form"):
    for criterion in criterion_order:
        # Forest green box for each stage/criterion
        st.markdown(
            f"""
            <div style='background:linear-gradient(90deg,#29522a 60%,#5fa66c 100%);padding:1rem 1.2rem 0.4rem 1.2rem;border-radius:1.1rem 1.1rem 0.4rem 0.4rem; margin-bottom:0.3rem; box-shadow: 0 1px 7px #29522a22;'>
                <span style='color:white;font-size:1.5rem;font-weight:700;letter-spacing:.02em;'>{criterion}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        group = df[df[2] == criterion].sort_values(by=0, key=lambda x: x.astype(int))
        for i, row in group.iterrows():
            label = row[3]
            # Component name: larger, bold, deep green
            st.markdown(
                f"<div style='font-size:1.2rem;font-weight:600;margin-top:0.6rem;margin-bottom:0.07rem;color:#29522a'>{int(row[0])}. {label}</div>",
                unsafe_allow_html=True
            )
            # Question text: darker, more readable
            st.markdown(
                f"<div style='font-size:1.05rem;color:#222; margin-bottom:0.2rem;'>{row[8]}</div>",
                unsafe_allow_html=True
            )
            # Additional info if any
            if row[9].strip():
                st.markdown(
                    f"<div style='font-size:0.97rem;color:#4a6849; margin-bottom:0.18rem;'>{row[9]}</div>",
                    unsafe_allow_html=True
                )
            # Answers
            answer = st.radio(
                label="",
                options=[
                    "",
                    ui.get("yes", "Yes"),
                    ui.get("partially", "Partially"),
                    ui.get("no", "No"),
                    ui.get("i_dont_know", "I don't know")
                ],
                index=0,
                key=f"q_{criterion}_{i}",
                horizontal=True
            )
            responses[f"{row[0]} - {label}"] = {
                "answer": answer,
                "label": label,
                "criterion": criterion,
                "order": row[0],
                "prompt": row[9],
                "definition": row[4],
                "example": row[5],
                "guiding": f"{row[6]}\n{row[7]}",
                "why_important": row[10],
                "how_to_address": row[11]
            }
            st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
    submitted = st.form_submit_button(
        ui.get("form_submit", "✅ Submit Quiz"),
        use_container_width=True
    )

if submitted:
    st.success(ui.get("thanks", "Thank you for completing the diagnostic! Download your results below and review the feedback."))
    st.markdown("---")

    if initiative_name:
        st.markdown(ui.get("results_for", "Results for: {initiative}").replace("{initiative}", initiative_name))

    summary_counts = pd.Series([v["answer"] for v in responses.values() if v["answer"]]).value_counts()
    not_answered_count = sum([1 for v in responses.values() if v['answer'] == ''])
    st.markdown(ui.get("summary_title", "Summary"))
    i_dont_know_label = ui.get('i_dont_know', "I don't know")
    not_answered_label = ui.get('not_answered', "Not answered")

    st.markdown(
        f"""
    - **{ui.get('yes', 'Yes')}**: {summary_counts.get(ui.get('yes', 'Yes'), 0)}
    - **{ui.get('partially', 'Partially')}**: {summary_counts.get(ui.get('partially', 'Partially'), 0)}
    - **{ui.get('no', 'No')}**: {summary_counts.get(ui.get('no', 'No'), 0)}
    - **{i_dont_know_label}**: {summary_counts.get(i_dont_know_label, 0)}
    - **{not_answered_label}**: {not_answered_count}
        """
    )

    
    
    
    # --- Excel Download ---
    csv_data = pd.DataFrame([
        {
            "Order": int(res["order"]),
            "Criterion": res["criterion"],
            "Component": res["label"],
            "Answer": res["answer"],
            "Prompt": res["prompt"]
        }
        for _, res in responses.items()
    ])
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        csv_data.to_excel(writer, index=False, sheet_name="Results")
    st.download_button(ui.get("download_results", "Download results as Excel"), data=excel_buffer.getvalue(), file_name="toc_diagnostic_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # --- Feedback ---
    # --- Feedback ---
    # --- Feedback ---
if not show_summary_only:
    st.markdown(
        "<div style='font-size:1.3rem;font-weight:700;color:#29522a;margin-top:1.4rem;margin-bottom:0.6rem;'>📝 Component-Level Feedback</div>",
        unsafe_allow_html=True
    )
    for criterion in criterion_order:
        st.markdown(
            f"""
            <div style='background:linear-gradient(90deg,#29522a 60%,#5fa66c 100%);padding:0.7rem 1.1rem 0.4rem 1.1rem;border-radius:1.1rem 1.1rem 0.5rem 0.5rem; margin-bottom:0.3rem; margin-top:1.0rem; box-shadow: 0 1px 7px #29522a22;'>
                <span style='color:white;font-size:1.15rem;font-weight:700;letter-spacing:.01em;'>{criterion}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        group = [res for res in responses.values() if res["criterion"] == criterion]
        group = sorted(group, key=lambda x: int(x["order"]))
        for res in group:
            label = res["label"]
            answer = res["answer"]
            order = int(res['order'])

            # Component title (HTML, big, bold)
            st.markdown(
                f"<div style='font-size:1.12rem;font-weight:700;color:#29522a;margin-top:0.7rem;margin-bottom:0.08rem'>{order}. {label}</div>",
                unsafe_allow_html=True
            )
            # Feedback chip (HTML)
            feedback_style = "border-radius:0.7rem;display:inline-block;padding:0.32rem 0.9rem 0.32rem 0.9rem; font-size:0.98rem; margin-bottom:0.26rem; margin-top:0.12rem; min-width:220px;"
            feedback_chip = ""
            if answer == ui.get("yes", "Yes"):
                feedback_chip = f"<div style='background:#e8f6ee;color:#29522a;{feedback_style}'>{ui.get('yes_label', '{component} is in place.').format(component=label)}</div>"
            elif answer == "":
                feedback_chip = f"<div style='background:#ede6d6;color:#ad7f1c;{feedback_style}'>{ui.get('not_answered_label', '{component} has not been answered.').format(component=label)}</div>"
            elif answer == ui.get("partially", "Partially"):
                feedback_chip = f"<div style='background:#faf7e1;color:#8b7000;{feedback_style}'>{ui.get('partially_label', '{component} needs improvement.').format(component=label)}</div>"
            elif answer == ui.get("no", "No"):
                feedback_chip = f"<div style='background:#fae7e7;color:#a43838;{feedback_style}'>{ui.get('no_label', '{component} is missing.').format(component=label)}</div>"
            elif answer == ui.get("i_dont_know", "I don't know"):
                feedback_chip = f"<div style='background:#ede6d6;color:#ab8800;{feedback_style}'>{ui.get('idk_label', '{component} status is unknown.').format(component=label)}</div>"

            st.markdown(feedback_chip, unsafe_allow_html=True)
            st.markdown("<div style='height:0.12rem;'></div>", unsafe_allow_html=True)

            # Feedback details: Markdown, so bold/italic etc. works
            if answer == ui.get("yes", "Yes"):
                st.markdown(
                    ui.get('use_as_reference', '').format(criterion=criterion),
                    unsafe_allow_html=False
                )
            elif answer == "":
                st.markdown(
                    f"{ui.get('why_it_matters_label', 'Why it matters:')} {res['why_important']}",
                    unsafe_allow_html=False
                )
                st.markdown(
                    f"{ui.get('how_to_address_label', 'How to address it:')} {res['how_to_address']}",
                    unsafe_allow_html=False
                )
            else:
                if answer == ui.get("partially", "Partially"):
                    st.markdown(
                        ui.get('to_strengthen', 'To strengthen your section, consider: {prompt}').format(criterion=criterion, prompt=res['prompt']),
                        unsafe_allow_html=False
                    )
                st.markdown(
                    f"{ui.get('why_it_matters_label', 'Why it matters:')} {res['why_important']}",
                    unsafe_allow_html=False
                )
                st.markdown(
                    f"{ui.get('how_to_address_label', 'How to address it:')} {res['how_to_address']}",
                    unsafe_allow_html=False
                )

            # Expander as before (HTML, for structured style)
            with st.expander(ui.get("learn_more", "📘 Learn more"), expanded=False):
                st.markdown(
                    f"<div style='font-size:0.98rem;padding-left:0.2rem;line-height:1.5;'>"
                    f"{ui.get('definition_label', '<b>Definition:</b>')} {res['definition']}<br>"
                    f"{ui.get('example_label', '<b>Example:</b>')} {res['example']}<br>"
                    f"{ui.get('guiding_questions_label', '<b>Guiding Questions:</b>')}<br>"
                    f"{res['guiding'].replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True
                )
            st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)



    st.markdown(ui.get("visual_map", "Visual Map of All Components"))
    visual_map = pd.DataFrame([
        {
            "Order": int(res["order"]),
            "Criterion": res["criterion"],
            "Component": res["label"],
            "Result": {
                ui.get("yes", "Yes"): "✅ Correct",
                ui.get("partially", "Partially"): "🔶 Needs Improvement",
                ui.get("no", "No"): "❌ Missing",
                ui.get("i_dont_know", "I don't know"): "❓ Unknown",
                "": "⬜ " + ui.get("not_answered", "Not answered")
            }.get(res["answer"], "⬜ " + ui.get("not_answered", "Not answered"))
        }
        for _, res in responses.items()
    ])
    
    
    
    visual_map = visual_map.sort_values("Order").reset_index(drop=True)
    st.dataframe(visual_map, use_container_width=True)
    st.markdown(ui.get("final_disclaimer", "This report is for reflection and internal use."))



from contact_me import render_footer

# at the very end of the page
render_footer(language=selected_language)