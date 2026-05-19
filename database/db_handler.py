import sqlite3
import json
from typing import List, Dict, Any, Optional

class DatabaseHandler:
    def __init__(self, db_path: str = "risk_control.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                occupation TEXT,
                monthly_income INTEGER,
                registration_date TEXT,
                extra_features TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_applications (
                app_id TEXT PRIMARY KEY,
                user_id TEXT,
                application_amount INTEGER,
                purpose TEXT,
                status TEXT,
                submitted_at TEXT,
                decision_at TEXT,
                final_credit_score REAL,
                final_amount INTEGER,
                reasoning TEXT,
                trace_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_history (
                record_id TEXT PRIMARY KEY,
                user_id TEXT,
                original_limit INTEGER,
                current_limit INTEGER,
                overdue_days INTEGER,
                total_repayment INTEGER,
                average_utilization REAL,
                last_updated TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_logs (
                log_id TEXT PRIMARY KEY,
                app_id TEXT,
                agent_name TEXT,
                action_type TEXT,
                input_data TEXT,
                output_data TEXT,
                timestamp TEXT,
                FOREIGN KEY (app_id) REFERENCES credit_applications(app_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user(self, user_data: Dict[str, Any]) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data.get('user_id'),
            user_data.get('name'),
            user_data.get('age'),
            user_data.get('occupation'),
            user_data.get('monthly_income'),
            user_data.get('registration_date'),
            json.dumps(user_data.get('extra_features', {}))
        ))
        conn.commit()
        conn.close()
        return True
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'name': row[1],
                'age': row[2],
                'occupation': row[3],
                'monthly_income': row[4],
                'registration_date': row[5],
                'extra_features': json.loads(row[6] if row[6] else '{}')
            }
        return None
    
    def save_credit_history(self, history: Dict[str, Any]) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO credit_history 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            history.get('record_id'),
            history.get('user_id'),
            history.get('original_limit', 0),
            history.get('current_limit', 0),
            history.get('overdue_days', 0),
            history.get('total_repayment', 0),
            history.get('average_utilization', 0),
            history.get('last_updated')
        ))
        conn.commit()
        conn.close()
        return True
    
    def get_credit_history(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_history WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'record_id': row[0],
                'user_id': row[1],
                'original_limit': row[2],
                'current_limit': row[3],
                'overdue_days': row[4],
                'total_repayment': row[5],
                'average_utilization': row[6],
                'last_updated': row[7]
            }
        return None
    
    def save_application(self, app_data: Dict[str, Any]) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO credit_applications 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            app_data.get('app_id'),
            app_data.get('user_id'),
            app_data.get('application_amount'),
            app_data.get('purpose'),
            app_data.get('status'),
            app_data.get('submitted_at'),
            app_data.get('decision_at'),
            app_data.get('final_credit_score'),
            app_data.get('final_amount'),
            app_data.get('reasoning', ''),
            json.dumps(app_data.get('trace_data', []))
        ))
        conn.commit()
        conn.close()
        return True
    
    def get_application(self, app_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_applications WHERE app_id = ?', (app_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'app_id': row[0],
                'user_id': row[1],
                'application_amount': row[2],
                'purpose': row[3],
                'status': row[4],
                'submitted_at': row[5],
                'decision_at': row[6],
                'final_credit_score': row[7],
                'final_amount': row[8],
                'reasoning': row[9],
                'trace_data': json.loads(row[10] if row[10] else '[]')
            }
        return None
    
    def save_decision_log(self, log_data: Dict[str, Any]) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO decision_logs 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data.get('log_id'),
            log_data.get('app_id'),
            log_data.get('agent_name'),
            log_data.get('action_type'),
            log_data.get('input_data'),
            json.dumps(log_data.get('output_data', {})),
            log_data.get('timestamp')
        ))
        conn.commit()
        conn.close()
        return True
    
    def query_applications_by_status(self, status: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_applications WHERE status = ?', (status,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'app_id': row[0],
                'user_id': row[1],
                'application_amount': row[2],
                'status': row[4]
            })
        return results
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, occupation FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        return [{'user_id': r[0], 'name': r[1], 'occupation': r[2]} for r in rows]