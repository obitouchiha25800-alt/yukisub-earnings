from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import calendar

app = Flask(__name__)
DATABASE = 'earnings.db'

def init_db():
    """Initialize the database with earnings table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_current_month_year():
    """Get current month name and year"""
    now = datetime.now()
    month_name = calendar.month_name[now.month]
    return month_name, now.year

def get_current_month_filter():
    """Get the current month and year for SQL filtering"""
    now = datetime.now()
    return now.month, now.year

@app.route('/')
def index():
    """Render the main dashboard"""
    month_name, year = get_current_month_year()
    return render_template('index.html', month=month_name, year=year)

@app.route('/api/earnings', methods=['GET'])
def get_earnings():
    """Get all earnings for the current month"""
    current_month, current_year = get_current_month_filter()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Fetch entries from current month only
    cursor.execute('''
        SELECT id, user_name, amount, created_at 
        FROM earnings 
        WHERE strftime('%m', created_at) = ? 
        AND strftime('%Y', created_at) = ?
        ORDER BY created_at DESC
    ''', (f'{current_month:02d}', str(current_year)))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Format data with DD/MM/YYYY date format
    earnings = []
    for row in rows:
        entry_date = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
        earnings.append({
            'id': row[0],
            'user_name': row[1],
            'amount': row[2],
            'date': entry_date.strftime('%d/%m/%Y')
        })
    
    # Calculate stats
    total_members = len(earnings)
    total_revenue = sum(e['amount'] for e in earnings)
    
    return jsonify({
        'earnings': earnings,
        'total_members': total_members,
        'total_revenue': total_revenue
    })

@app.route('/api/earnings', methods=['POST'])
def add_earning():
    """Add a new earning entry"""
    data = request.get_json()
    user_name = data.get('user_name', '').strip()
    amount = data.get('amount', 49)
    
    if not user_name:
        return jsonify({'error': 'User name is required'}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Insert with current timestamp (auto-detected)
    cursor.execute('''
        INSERT INTO earnings (user_name, amount, created_at)
        VALUES (?, ?, ?)
    ''', (user_name, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/earnings/<int:entry_id>', methods=['DELETE'])
def delete_earning(entry_id):
    """Delete an earning entry"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM earnings WHERE id = ?', (entry_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
