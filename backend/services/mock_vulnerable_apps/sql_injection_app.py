"""
Mock SQL Injection Vulnerable App
Intentionally vulnerable for Wargaming validation - DO NOT USE IN PRODUCTION
"""
from fastapi import FastAPI, Query
import sqlite3

app = FastAPI(title="Mock SQL Injection App")

# Create in-memory database with test data
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT
        )
    ''')
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'secret123', 'admin@example.com')")
    cursor.execute("INSERT INTO users VALUES (2, 'user', 'pass456', 'user@example.com')")
    conn.commit()
    return conn

db_conn = init_db()

@app.get("/")
def root():
    return {"app": "sql_injection_vulnerable", "status": "vulnerable"}

@app.get("/api/users")
def get_user(user_id: str = Query("1")):
    """INTENTIONALLY VULNERABLE - No input sanitization"""
    try:
        cursor = db_conn.cursor()
        # VULNERABILITY: Direct string concatenation
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchall()
        
        if result:
            return {
                "success": True,
                "users": [
                    {"id": r[0], "username": r[1], "email": r[3]}
                    for r in result
                ],
                "query": query  # Leak query for exploit verification
            }
        return {"success": False, "users": [], "query": query}
    except Exception as e:
        return {"success": False, "error": str(e), "query": query}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9081)
