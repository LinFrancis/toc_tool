import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Setup ---
st.set_page_config(page_title="Theory of Change Tool", layout="wide")

st.title("📘 Theory of Change Dataset Viewer")

# --- Load credentials from secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
gc = gspread.authorize(creds)

# --- Load spreadsheet ---
spreadsheet = gc.open_by_key("1q_FFt5BUF1z7w2NOO960elmPiUNbO76T9r6F0Bi2tJ0")
sheet_names = [ws.title for ws in spreadsheet.worksheets()]
selected_sheet = st.selectbox("Select a worksheet", sheet_names)

worksheet = spreadsheet.worksheet(selected_sheet)
records = worksheet.get_all_records()
df = pd.DataFrame(records)

# --- Display ---
st.success(f"Loaded {len(df)} rows from sheet: {selected_sheet}")
st.dataframe(df, use_container_width=True)
