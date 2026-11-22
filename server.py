import sqlite3
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')
DB_PATH = 'zentrik.db'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            emp_id TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            installed INTEGER DEFAULT 0,
            device TEXT DEFAULT 'Not Installed',
            terms_accepted INTEGER DEFAULT 0,
            duty_on INTEGER DEFAULT 0,
            attendance TEXT DEFAULT 'Leave',
            check_in_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            runner_id TEXT NOT NULL,
            title TEXT NOT NULL,
            from_name TEXT NOT NULL,
            to_name TEXT NOT NULL,
            trip_type TEXT NOT NULL,
            assigned_by TEXT NOT NULL,
            description TEXT NOT NULL,
            distance_km REAL NOT NULL,
            status TEXT NOT NULL,
            started_at_ms INTEGER,
            proof_note TEXT,
            reject_reason TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS leaves (
            id TEXT PRIMARY KEY,
            runner_id TEXT NOT NULL,
            leave_date TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            who TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    ''')
    seed_users = [
        ('adm0', 'ZK-ADM-00', '9900000000', 'Welcome@999', 'Master Owner (Admin)', 'admin', 1, 'Admin Console', 1, 1, 'Present', '08:00 AM'),
        ('bm1', 'ZK-BM-01', '9811100001', 'Welcome@BM1', 'Rajesh Sharma (BM)', 'owner', 1, 'Web Portal', 1, 1, 'Present', '08:15 AM'),
        ('dbm2', 'ZK-DBM-02', '9811100002', 'Welcome@DBM', 'Sneha Verma (DBM)', 'owner', 1, 'Web Portal', 1, 1, 'Present', '08:20 AM'),
        ('r1', 'ZK-RUN-101', '9876543210', 'Welcome@101', 'Samil Hussain', 'runner', 1, 'Android 14', 1, 1, 'Present', '08:30 AM'),
        ('r2', 'ZK-RUN-102', '9876543211', 'Welcome@102', 'Priya Nair', 'runner', 1, 'Android 13', 1, 1, 'Present', '08:40 AM'),
        ('r3', 'ZK-RUN-103', '9876543212', 'Welcome@103', 'Arjun Kumar', 'runner', 0, 'Not Installed', 0, 0, 'Leave', None),
    ]
    cur.executemany(
        'INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
        seed_users
    )
    conn.commit()
    conn.close()


@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    ident = (data.get('identifier') or '').strip()
    pw = (data.get('password') or '').strip()
    role = data.get('role')
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE (LOWER(emp_id)=LOWER(?) OR phone=?) AND password=? AND role=?',
        (ident, ident, pw, role)
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    conn.execute('UPDATE users SET installed=1, terms_accepted=1 WHERE id=?', (user['id'],))
    conn.execute(
        'INSERT INTO activity_logs (who, action, created_at) VALUES (?, ?, ?)',
        (f"{user['name']} ({user['emp_id']})", 'Logged in & accepted Terms', time.strftime('%I:%M %p'))
    )
    conn.commit()
    conn.close()
    return jsonify(dict(user))


@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks_api():
    conn = get_db()
    if request.method == 'GET':
        rows = [dict(r) for r in conn.execute('SELECT * FROM tasks ORDER BY rowid DESC').fetchall()]
        conn.close()
        return jsonify(rows)
    d = request.json or {}
    tid = d.get('id') or f"BR-{int(time.time()) % 10000}"
    conn.execute(
        '''INSERT INTO tasks (id, runner_id, title, from_name, to_name, trip_type, assigned_by, description, distance_km, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (tid, d['runner_id'], d['title'], d['from_name'], d['to_name'], d['trip_type'],
         d['assigned_by'], d['description'], d['distance_km'], 'Created', time.strftime('%d-%b-%Y'))
    )
    conn.commit()
    conn.close()
    return jsonify({'id': tid, 'status': 'Created'}), 201


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
