"""
Evaluation Manager - Persistent storage and analytics for participant feedback.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class EvaluationManager:
    """Manages evaluation responses with SQLite persistence."""
    
    DB_PATH = "evaluation_responses.db"
    
    def __init__(self):
        """Initialize the database if it doesn't exist."""
        self._init_db()
    
    def _init_db(self):
        """Create database and table if they don't exist."""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                participant_id TEXT NOT NULL,
                preference TEXT NOT NULL,
                method_a_helpfulness INTEGER,
                method_b_helpfulness INTEGER,
                method_a_understandability INTEGER,
                method_b_understandability INTEGER,
                method_a_speed INTEGER,
                method_b_speed INTEGER,
                method_a_practical INTEGER,
                method_b_practical INTEGER,
                comments TEXT,
                data_source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_response(self, response: Dict) -> bool:
        """Save a single evaluation response to the database."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO responses (
                    timestamp, participant_id, preference,
                    method_a_helpfulness, method_b_helpfulness,
                    method_a_understandability, method_b_understandability,
                    method_a_speed, method_b_speed,
                    method_a_practical, method_b_practical,
                    comments, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response['timestamp'],
                response['participant_id'],
                response['preference'],
                response.get('method_a_helpfulness', 0),
                response.get('method_b_helpfulness', 0),
                response.get('method_a_understandability', 0),
                response.get('method_b_understandability', 0),
                response.get('method_a_speed', 0),
                response.get('method_b_speed', 0),
                response.get('method_a_practical', 0),
                response.get('method_b_practical', 0),
                response.get('comments', ''),
                response.get('data_source', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving response: {e}")
            return False
    
    def get_all_responses(self) -> pd.DataFrame:
        """Retrieve all responses as a pandas DataFrame."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            df = pd.read_sql_query(
                "SELECT * FROM responses ORDER BY created_at DESC",
                conn
            )
            conn.close()
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Error retrieving responses: {e}")
            return pd.DataFrame()
    
    def get_response_count(self) -> int:
        """Get total number of responses."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM responses")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Error counting responses: {e}")
            return 0
    
    def get_analytics(self) -> Dict:
        """Get aggregate analytics from all responses."""
        df = self.get_all_responses()
        
        if df.empty:
            return {}
        
        analytics = {
            'total_responses': len(df),
            'method_a_avg_helpfulness': df['method_a_helpfulness'].mean(),
            'method_b_avg_helpfulness': df['method_b_helpfulness'].mean(),
            'method_a_avg_understandability': df['method_a_understandability'].mean(),
            'method_b_avg_understandability': df['method_b_understandability'].mean(),
            'method_a_avg_speed': df['method_a_speed'].mean(),
            'method_b_avg_speed': df['method_b_speed'].mean(),
            'method_a_avg_practical': df['method_a_practical'].mean(),
            'method_b_avg_practical': df['method_b_practical'].mean(),
            'preference_counts': df['preference'].value_counts().to_dict(),
            'data_source_counts': df['data_source'].value_counts().to_dict(),
        }
        
        return analytics
    
    def delete_all_responses(self) -> bool:
        """Delete all responses from the database."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM responses")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting responses: {e}")
            return False
    
    def export_to_csv(self, filename: Optional[str] = None) -> Optional[str]:
        """Export all responses to CSV file."""
        df = self.get_all_responses()
        
        if df.empty:
            return None
        
        if filename is None:
            filename = f"evaluation_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            df.to_csv(filename, index=False)
            return filename
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
