import os
import shutil
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def webkit_timestamp_to_datetime(timestamp):
    """Converts a 17-digit WebKit microsecond timestamp to readable UTC time."""
    if timestamp == 0 or pd.isna(timestamp):
        return "N/A"
    try:
        epoch_start = datetime(1601, 1, 1)
        delta = timedelta(microseconds=timestamp)
        return (epoch_start + delta).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return "Invalid Timestamp"

def extract_history(browser_name, raw_path):
    """Safely copies and parses an individual browser history database."""
    full_path = os.path.expanduser(raw_path)
    temp_db = f"temp_{browser_name.lower()}_history.db"
    
    print(f"🔎 Scanning for {browser_name} data...")
    
    if not os.path.exists(full_path):
        print(f"⚠️ {browser_name} history file not found at standard path. Skipping.")
        return None

    try:
        # Prevent "Database Locked" errors if the browser is currently running
        shutil.copyfile(full_path, temp_db)
        
        # Connect and extract data
        conn = sqlite3.connect(temp_db)
        query = """
        SELECT url, title, visit_count, last_visit_time 
        FROM urls 
        ORDER BY last_visit_time DESC;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Add source identifier
        df['source_browser'] = browser_name
        return df
        
    except Exception as e:
        print(f"❌ Error processing {browser_name}: {e}")
        return None
    finally:
        # Housekeeping: Wipe temporary file from disk
        if os.path.exists(temp_db):
            os.remove(temp_db)

def main():
    print("🕵️‍♂️ Starting Automated Forensic Browser Artifact Extraction...")
    
    targets = {
        "Microsoft Edge": r"~\AppData\Local\Microsoft\Edge\User Data\Default\History",
        "Google Chrome": r"~\AppData\Local\Google\Chrome\User Data\Default\History"
    }
    
    extracted_dataframes = []
    
    for browser, path in targets.items():
        df = extract_history(browser, path)
        if df is not None and not df.empty:
            extracted_dataframes.append(df)
            
    if not extracted_dataframes:
        print("❌ No browser history data could be retrieved from this machine.")
        return
        
    master_df = pd.concat(extracted_dataframes, ignore_index=True)
    
    print("⏰ Normalizing chronological timelines...")
    master_df['readable_visit_time'] = master_df['last_visit_time'].apply(webkit_timestamp_to_datetime)
    master_df = master_df.drop(columns=['last_visit_time'])
    
    master_df = master_df.sort_values(by='readable_visit_time', ascending=False)
    
    output_name = "Forensic_Browser_Timeline.xlsx"
    master_df.to_excel(output_name, index=False)
    print(f"🎉 Success! Combined timeline saved to: {output_name}")

if __name__ == "__main__":
    main()
