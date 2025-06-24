
import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

# Load UI labels from JSON
with open("ui_contact.json", "r", encoding="utf-8") as f:
    CONTACT_TEXT = json.load(f)

# Google Sheet config
SHEET_ID = "1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0"
SHEET_NAME = "contact_messages"

# Auth once
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope)
    return gspread.authorize(credentials)

def render_footer(language="English"):
    ui = CONTACT_TEXT.get(language, CONTACT_TEXT["English"])
    st.markdown("---")
    



    with st.form("contact_form"):
        st.markdown(f"<strong>{ui['footer_note']}</strong>", unsafe_allow_html=True)

        st.markdown(f"### {ui['form_title']}")
        name = st.text_input(ui["name"])
        email = st.text_input(ui["email"])
        subject = st.text_input(ui["subject"])
        content = st.text_area(ui["content"])
        submitted = st.form_submit_button(ui["submit"])

        if submitted:
            if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z]+$", email):
                st.warning(ui["invalid_email"])
                return

            # Prepare data row
            timestamp = datetime.utcnow().isoformat()
            row = [timestamp, language, name, email, subject, content]

            try:
                client = get_gspread_client()
                sheet = client.open_by_key(SHEET_ID)
                try:
                    worksheet = sheet.worksheet(SHEET_NAME)
                except gspread.exceptions.WorksheetNotFound:
                    worksheet = sheet.add_worksheet(title=SHEET_NAME, rows="100", cols="10")
                    worksheet.append_row(["Timestamp", "Language", "Name", "Email", "Subject", "Content"])
                worksheet.append_row(row)
                st.success(ui["success"])
                with st.expander("📄 " + ui["success"]):
                    st.write("**Name:**", name)
                    st.write("**Email:**", email)
                    st.write("**Subject:**", subject)
                    st.write("**Message:**", content)
            except Exception as e:
                st.error("❌ Failed to send message. Please try again later.")
                st.exception(e)
