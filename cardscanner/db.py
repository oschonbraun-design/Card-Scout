import sqlite3

def connect(path="scanner.db"):
    db=sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS seen(item_id TEXT PRIMARY KEY, first_seen TEXT DEFAULT CURRENT_TIMESTAMP, title TEXT, price REAL)")
    return db

def is_new(db, item_id, title, price):
    try:
        db.execute("INSERT INTO seen(item_id,title,price) VALUES(?,?,?)",(item_id,title,price)); db.commit(); return True
    except sqlite3.IntegrityError: return False
