#!/usr/bin/env python3
"""
Minimal XSS Vulnerable App - FOR TESTING ONLY.

INTENTIONALLY VULNERABLE - DO NOT USE IN PRODUCTION.
"""

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <h1>Vulnerable XSS App</h1>
    <form action="/search" method="GET">
        <input type="text" name="q" placeholder="Search...">
        <button type="submit">Search</button>
    </form>
    <p><a href='/search?q=<script>alert("XSS")</script>'>Test XSS</a></p>
    """

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    # INTENTIONALLY VULNERABLE - No escaping!
    html = f"""
    <h1>Search Results</h1>
    <p>You searched for: {query}</p>
    <p><a href="/">Back</a></p>
    """
    
    return html  # VULNERABLE - Raw HTML with user input!

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
