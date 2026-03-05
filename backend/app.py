from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
from pathlib import Path

from tools.Development_tools.dbCreator import Database
from tools.dbConnector import DBConnector
from router import register_routes
from logging import log

db_path = "data.db"
db = Database(db_path)
db_connector = None
app = Flask(__name__)

app.config['SWAGGER'] = {
    'title': 'Lerngruppentool API',
    'uiversion': 3,
    'openapi': '3.0.2',
}

swagger_spec_path = Path(__file__).resolve().parent / 'api_docs.yaml'
swagger = Swagger(app, template_file=str(swagger_spec_path))

# CORS für alle Routen und Methoden erlauben (löst den "Blocked by CORS" Fehler)
CORS(app, resources={r"/*": {"origins": "*"}}, 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Auth-Email", "X-Auth-Password-Hash"])

def setup_db(add_test_data: bool = False):
    global db_connector
    db.init_db()
    if add_test_data:
        db.populate_test_data()
    try:
        db_connector = DBConnector(db_path)
        print("DB connection test: OK")
    except Exception as e:
        log(f"DB connection test failed: {str(e)}", "error")
        print(f"DB connection test failed: {e}")
        raise
    print("Datenbank bereit.")

@app.route('/', methods=['GET'])
def index():
        """
        API Status
        ---
        tags:
            - Health
        responses:
            200:
                description: API läuft erfolgreich
        """
        return jsonify({
        "status": "success",
        "message": "Lerngruppentool API läuft!",
        "version": "1.0",
        "endpoints": {
            "Swagger-UI": "/apidocs",
            "users": "/api/users",
            "groups": "/api/groups",
            "join_requests": "/api/join-requests",
            "login": "/login",      
            "register": "/users"       
        }
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"message": "Route nicht gefunden", "error": str(e)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"message": "Interner Serverfehler", "error": str(e)}), 500

if __name__ == '__main__':
    setup_db(True)  # Set to True to populate test data on startup
    
    # 2. DANN Routen registrieren
    register_routes(app, db_connector)
    
    print("Server läuft auf http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
