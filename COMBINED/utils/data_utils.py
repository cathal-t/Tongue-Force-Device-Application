# utils/data_utils.py

import os
import re

def get_patient_ids(profiles_dir='profiles'):
    """Returns a list of patient IDs (folder names) in the profiles directory."""
    if not os.path.exists(profiles_dir):
        return []
    return [f for f in os.listdir(profiles_dir) if os.path.isdir(os.path.join(profiles_dir, f))]

def get_sessions_for_patient(patient_id, profiles_dir='profiles'):
    """Returns a list of session filenames for the given patient ID."""
    patient_folder = os.path.join(profiles_dir, patient_id)
    if not os.path.exists(patient_folder):
        return []
    # List CSV files in the patient folder
    files = [f for f in os.listdir(patient_folder) if f.endswith('.csv')]
    # Extract timestamp from filenames
    sessions = []
    for f in files:
        match = re.match(r'.+_(\d{8}_\d{6})\.csv', f)
        if match:
            timestamp_str = match.group(1)
            timestamp_formatted = f"{timestamp_str[:4]}-{timestamp_str[4:6]}-{timestamp_str[6:8]} {timestamp_str[9:11]}:{timestamp_str[11:13]}:{timestamp_str[13:]}"
            sessions.append({'label': timestamp_formatted, 'value': f})
        else:
            sessions.append({'label': f, 'value': f})
    return sessions
