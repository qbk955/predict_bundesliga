# utils/gsheets.py

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
import os
import sys

def init_gsheets():
    """
    Initialize the Google Sheets client using service account credentials.
    Returns the 'Scoreboard' worksheet.
    """
    # Define the scope
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Determine the path to the credentials file
    # Assumes that gsheets.py is inside the utils/ directory
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    
    # Create credentials using the service account info stored in Streamlit secrets
    credentials_path = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scopes
)

    # Check if the credentials file exists
    if not os.path.exists(credentials_path):
        st.error(f"Service account credentials file not found at path: {credentials_path}")
        st.stop()

    # Create credentials using the service account file
    try:
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=scopes
        )
    except Exception as e:
        st.error(f"Error creating credentials from file: {e}")
        st.stop()

    # Authorize the client
    try:
        client = gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Error authorizing gspread client: {e}")
        st.stop()

    # Open the Google Sheet by Spreadsheet ID
    SPREADSHEET_ID = '1hQgm_XhoakMVVoi7vCXwa4MXKSOPkv59VWIVm3MhM2E'  # Replace with your actual Spreadsheet ID
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Google Spreadsheet not found. Please check the Spreadsheet ID.")
        st.stop()
    except Exception as e:
        st.error(f"Error opening Google Spreadsheet: {e}")
        st.stop()

    # Select the worksheet named 'Scoreboard'
    try:
        sheet = spreadsheet.worksheet('Scoreboard')
    except gspread.exceptions.WorksheetNotFound:
        # If the worksheet doesn't exist, create it
        try:
            sheet = spreadsheet.add_worksheet(title='Scoreboard', rows="1000", cols="2")
            sheet.append_row(['Username', 'Score'])  # Add headers
        except Exception as e:
            st.error(f"Error creating 'Scoreboard' worksheet: {e}")
            st.stop()
    except Exception as e:
        st.error(f"Error accessing 'Scoreboard' worksheet: {e}")
        st.stop()
    
    return sheet



def save_scoreboard(sheet, scoreboard):
    """
    Save the scoreboard DataFrame to Google Sheets.
    """
    try:
        # Clear existing data except headers
        sheet.resize(rows=1)
        # Append all rows at once
        rows = scoreboard.values.tolist()
        sheet.append_rows(rows, value_input_option='RAW')
    except Exception as e:
        st.error(f"Error saving scoreboard to Google Sheets: {e}")
        
def load_scoreboard(sheet):
    """
    Load the scoreboard from the Google Sheets.
    Returns a sorted DataFrame.
    """
    try:
        records = sheet.get_all_records()
        scoreboard = pd.DataFrame(records)
        # Ensure columns exist
        expected_columns = ['Username', 'Score']
        for col in expected_columns:
            if col not in scoreboard.columns:
                st.warning(f"Column '{col}' missing in Google Sheet. Re-initializing the scoreboard.")
                sheet.clear()
                sheet.append_row(expected_columns)
                return pd.DataFrame(columns=expected_columns)
        # Sort the scoreboard descending by 'Score'
        scoreboard = scoreboard.sort_values(by='Score', ascending=False).reset_index(drop=True)
        return scoreboard
    except Exception as e:
        st.error(f"Error loading scoreboard from Google Sheets: {e}")
        return pd.DataFrame(columns=['Username', 'Score'])
