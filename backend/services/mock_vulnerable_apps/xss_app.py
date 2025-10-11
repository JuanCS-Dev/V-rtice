"""
Mock XSS Vulnerable App
Intentionally vulnerable for Wargaming validation - DO NOT USE IN PRODUCTION
"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Mock XSS App")

@app.get("/")
def root():
    return {"app": "xss_vulnerable", "status": "vulnerable"}

@app.get("/api/search", response_class=HTMLResponse)
def search(q: str = Query("")):
    """INTENTIONALLY VULNERABLE - No output encoding"""
    # VULNERABILITY: Direct embedding of user input in HTML
    html = f"""
    <html>
        <head><title>Search Results</title></head>
        <body>
            <h1>Search Results</h1>
            <p>You searched for: {q}</p>
            <div id="results">
                <p>No results found for "{q}"</p>
            </div>
        </body>
    </html>
    """
    return html

@app.get("/api/comment")
def post_comment(comment: str = Query("")):
    """INTENTIONALLY VULNERABLE - Stored XSS"""
    # VULNERABILITY: No sanitization, returns HTML with user input
    return {
        "success": True,
        "rendered_html": f'<div class="comment">{comment}</div>',
        "comment": comment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9082)
