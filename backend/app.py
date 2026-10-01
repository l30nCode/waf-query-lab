import sqlite3
from flask import Flask, request

app = Flask(__name__)

DATABASE = "test_database.db"
BODY_REQUESTS = ["POST", "QUERY"]

def extract_search_id():
    if request.method == "GET":
        id = request.args.get("id")
        
        if not id:
            return None
        
        return id
    
    if request.method in BODY_REQUESTS:
        data = request.get_json(silent=True)
        
        if not data:
            return None
        
        id = data.get("id")
        
        if not id:
            return None
        
        return id
    
    return None

@app.route("/search", methods=["GET", "POST", "QUERY"])
def search_id():
    method = request.method
    content_type = request.content_type
    raw_body = request.get_data(as_text=True)    
    
    search_id = extract_search_id()
    
    if search_id is None:
        return {
            "error": "No Search-ID provided.",
            "method": method
        }, 400
    
    sql = f"""
        SELECT id, name
        FROM users
        WHERE id = {search_id}
    """
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute(sql)
            
            rows = cursor.fetchall()    

        return {
                "sql": sql,
                "search_id": search_id, 
                "method": method, 
                "content_type": content_type, 
                "raw_body": raw_body,
                "result": [dict(row) for row in rows]
            }
        
    except sqlite3.Error as error:
        return {
            "error": f"Could not fetch data due to error: {error}.",
            "method": method,
        }, 500
    
if __name__ == "__main__":
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True
    )