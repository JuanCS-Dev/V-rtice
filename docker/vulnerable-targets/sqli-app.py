#!/usr/bin/env python3
"""
Minimal SQL Injection Vulnerable App - FOR TESTING ONLY.

INTENTIONALLY VULNERABLE - DO NOT USE IN PRODUCTION.
"""

from flask import Flask, request
import sqlite3

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('/tmp/test.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT, email TEXT)''')
    c.execute("INSERT INTO users VALUES (1, 'admin', 'admin@test.com')")
    c.execute("INSERT INTO users VALUES (2, 'user', 'user@test.com')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return """
    <h1>Vulnerable SQL Query App</h1>
    <p>Test: <a href="/user?id=1">/user?id=1</a></p>
    <p>Exploit: <a href="/user?id=1' OR '1'='1">/user?id=1' OR '1'='1</a></p>
    """

@app.route('/user')
def user():
    user_id = request.args.get('id', '')
    
    # INTENTIONALLY VULNERABLE - No sanitization!
    query = f"SELECT * FROM users WHERE id = {user_id}"
    
    try:
        conn = sqlite3.connect('/tmp/test.db')
        c = conn.cursor()
        c.execute(query)  # VULNERABLE!
        results = c.fetchall()
        conn.close()
        
        if results:
            output = "<h2>Query Results:</h2><ul>"
            for row in results:
                output += f"<li>ID: {row[0]}, Name: {row[1]}, Email: {row[2]}</li>"
            output += "</ul>"
            output += f"<p><small>Query: {query}</small></p>"
            return output
        else:
            return "<p>No results found</p>"
            
    except Exception as e:
        # VULNERABLE - Expose SQL errors!
        return f"<h2>SQL Error:</h2><pre>{str(e)}</pre><p>Query: {query}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
