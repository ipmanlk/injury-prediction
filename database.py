import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATABASE_NAME = MODELS_DIR = Path(__file__).parent / "data" / "user_data.db"

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            created_time TIMESTAMP,
            heartRate REAL,
            oxygenSaturation REAL,
            temperature REAL,
            systolicBloodPressure REAL,
            diastolicBloodPressure REAL,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def store_user_data(uid, data):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    abnormal_count = 0

    if data['heartRate'] < 50 or data['heartRate'] > 130:
        abnormal_count += 1

    if data['oxygenSaturation'] < 90 or data['oxygenSaturation'] > 100:
        abnormal_count += 1
    
    if data['temperature'] < 31 or data['temperature'] > 38:
        abnormal_count += 1

    if data['systolicBloodPressure'] < 90 or data['systolicBloodPressure'] > 160:
        abnormal_count += 1

    if data['diastolicBloodPressure'] < 60 or data['diastolicBloodPressure'] > 110:
        abnormal_count += 1

    if abnormal_count >= 2:
        data['status'] = "Abnormal"
    else:
        data['status'] = "Normal"

    created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO sensor_data (
            uid, created_time, heartRate, oxygenSaturation, temperature,
            systolicBloodPressure, diastolicBloodPressure, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        uid, created_time, data['heartRate'], data['oxygenSaturation'],
        data['temperature'], data['systolicBloodPressure'],
        data['diastolicBloodPressure'], data['status']
    ))
    
    conn.commit()
    conn.close()

def get_user_data(uid):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    week_ago = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        SELECT * FROM sensor_data
        WHERE uid = ? AND created_time >= ?
    ''', (uid, week_ago))
    
    data = cursor.fetchall()
    
    conn.close()
    
    return data

def check_user_data(uid):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT MIN(created_time) FROM sensor_data
        WHERE uid = ?
    ''', (uid,))
    
    oldest_record_time = cursor.fetchone()[0]
    
    if oldest_record_time is not None:
        week_ago = (datetime.now() - timedelta(weeks=1))
        oldest_record_time = datetime.strptime(oldest_record_time, '%Y-%m-%d %H:%M:%S')
        
        conn.close()
        
        return oldest_record_time <= week_ago
    
    conn.close()
    
    return False
