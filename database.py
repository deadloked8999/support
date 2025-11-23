import sqlite3
from datetime import datetime
from config import DATABASE_NAME


def init_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            phone TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payment_received INTEGER DEFAULT 0,
            receipt_file_id TEXT,
            serial_number TEXT,
            serial_photo_file_id TEXT,
            box_serial_number TEXT,
            box_serial_photo_file_id TEXT,
            kit_number TEXT,
            status TEXT DEFAULT 'pending',
            service_provided INTEGER DEFAULT 0,
            service_provided_at TEXT,
            last_reminder_day INTEGER
        )
    ''')
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN serial_number TEXT
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN serial_photo_file_id TEXT
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN box_serial_number TEXT
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN box_serial_photo_file_id TEXT
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN last_reminder_day INTEGER
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN service_provided INTEGER DEFAULT 0
        ''')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('''
            ALTER TABLE activations ADD COLUMN service_provided_at TEXT
        ''')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


def add_purchase(user_id, phone, name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO purchases (user_id, phone, name, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, phone, name, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def add_activation(user_id, phone, name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activations (user_id, phone, name, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, phone, name, datetime.now().isoformat()))
    conn.commit()
    activation_id = cursor.lastrowid
    conn.close()
    return activation_id


def update_activation_receipt(user_id, receipt_file_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET payment_received = 1, receipt_file_id = ?, status = 'payment_confirmed'
        WHERE user_id = ? AND status = 'pending'
    ''', (receipt_file_id, user_id))
    conn.commit()
    conn.close()


def update_activation_serial_number(user_id, serial_number):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET serial_number = ?
        WHERE user_id = ? AND serial_number IS NULL
    ''', (serial_number, user_id))
    conn.commit()
    conn.close()


def update_activation_serial_photo(user_id, photo_file_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET serial_photo_file_id = ?
        WHERE user_id = ? AND serial_photo_file_id IS NULL
    ''', (photo_file_id, user_id))
    conn.commit()
    conn.close()


def update_activation_box_serial_number(user_id, box_serial_number):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET box_serial_number = ?
        WHERE user_id = ? AND box_serial_number IS NULL
    ''', (box_serial_number, user_id))
    conn.commit()
    conn.close()


def update_activation_box_serial_photo(user_id, photo_file_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET box_serial_photo_file_id = ?
        WHERE user_id = ? AND box_serial_photo_file_id IS NULL
    ''', (photo_file_id, user_id))
    conn.commit()
    conn.close()


def update_activation_kit(user_id, kit_number):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET kit_number = ?, status = 'completed'
        WHERE user_id = ? AND status = 'payment_confirmed'
    ''', (kit_number, user_id))
    conn.commit()
    conn.close()


def get_all_purchases():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, phone, name, created_at
        FROM purchases
        ORDER BY created_at DESC
    ''')
    purchases = cursor.fetchall()
    conn.close()
    return purchases


def get_all_activations():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, phone, name, created_at, payment_received, 
               receipt_file_id, serial_number, serial_photo_file_id, 
               box_serial_number, box_serial_photo_file_id, kit_number, 
               status, service_provided, service_provided_at
        FROM activations
        ORDER BY created_at DESC
    ''')
    activations = cursor.fetchall()
    conn.close()
    return activations


def mark_service_provided(activation_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET service_provided = 1, service_provided_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), activation_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_activations_for_subscription_reminders():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, phone, name, service_provided_at, last_reminder_day
        FROM activations
        WHERE service_provided = 1 AND service_provided_at IS NOT NULL
    ''')
    activations = cursor.fetchall()
    conn.close()
    return activations


def update_last_reminder_day(activation_id, days_left):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activations 
        SET last_reminder_day = ?
        WHERE id = ?
    ''', (days_left, activation_id))
    conn.commit()
    conn.close()


def get_statistics():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM purchases')
    total_purchases = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM activations')
    total_activations = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM activations WHERE status = "pending"')
    pending_activations = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM activations WHERE status = "payment_confirmed"')
    payment_confirmed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM activations WHERE status = "completed"')
    completed_activations = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total_purchases': total_purchases,
        'total_activations': total_activations,
        'pending_activations': pending_activations,
        'payment_confirmed': payment_confirmed,
        'completed_activations': completed_activations
    }

