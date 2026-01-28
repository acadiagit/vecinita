"""
================================================================================
MODULE: query_logger.py
DESCRIPTION: Logs user queries and agent responses to a CSV file.
             Includes standalone testing logic.
AUTHOR: Vecinita Dev Team
DATE: 2026-01-25
================================================================================
"""

import csv
import os
import sys
from datetime import datetime

# Path to the log file (Relative to where python runs)
LOG_FILE = "logs/query_response.csv"
MAX_ROWS = 1000

def log_interaction(query: str, response: str):
    """
    Logs the Q&A pair to a CSV file.
    Args:
        query (str): The user's question.
        response (str): The agent's answer.
    """
    # --- DEBUG PRINTS ---
    print(f"\n[LOGGER DEBUG] Starting log_interaction...", file=sys.stdout)
    
    # 1. Print absolute path so we know EXACTLY where it is going
    abs_path = os.path.abspath(LOG_FILE)
    print(f"[LOGGER DEBUG] Target file path: {abs_path}", file=sys.stdout)

    try:
        # 2. Ensure directory exists
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            print(f"[LOGGER DEBUG] Directory '{log_dir}' missing. Creating it...", file=sys.stdout)
            os.makedirs(log_dir, exist_ok=True)
        
        rows = []
        
        # 3. Read existing logs
        if os.path.exists(LOG_FILE):
            print(f"[LOGGER DEBUG] File exists. Reading...", file=sys.stdout)
            try:
                with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            except Exception as e:
                print(f"[LOGGER DEBUG] Error reading: {e}", file=sys.stdout)

        # 4. Append new entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_query = query.replace('\n', ' ').strip()
        clean_response = response.replace('\n', ' ').strip()
        
        rows.append([timestamp, clean_query, clean_response])

        # 5. FIFO Truncate
        if len(rows) > MAX_ROWS:
            rows = rows[-MAX_ROWS:]

        # 6. Write back
        print(f"[LOGGER DEBUG] Writing {len(rows)} rows to file...", file=sys.stdout)
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            
        print(f"[LOGGER DEBUG] SUCCESS! Log written.\n", file=sys.stdout)

    except Exception as e:
        print(f"[LOGGER DEBUG] FATAL ERROR in logger: {e}\n", file=sys.stdout)

# ==============================================================================
# STANDALONE TEST BLOCK
# ==============================================================================
if __name__ == "__main__":
    print("--- STANDALONE TEST START ---")
    
    # 1. Execute the function
    log_interaction("Manual Python Test", "If you see this, the code works.")
    
    # 2. Verify Result
    if os.path.exists(LOG_FILE):
        print(f"✅ Verified: {LOG_FILE} was created successfully.")
        print(f"📍 Absolute Path: {os.path.abspath(LOG_FILE)}")
        
        # Optional: Print content to prove it
        with open(LOG_FILE, 'r') as f:
            print(f"📄 File Content: {f.read().strip()}")
    else:
        print("❌ FAILED: File was not created.")
        
    print("--- STANDALONE TEST END ---")

# END OF FILE
