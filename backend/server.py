from flask import Flask, jsonify
from flask_cors import CORS
from cache import get_word_to_level_map # <-- IMPORT FROM NEW FILE

app = Flask(__name__)
CORS(app)

# --- Import and Register Blueprints ---
from routes.quiz_routes import quiz_bp
from routes.update_routes import update_bp
from routes.report_routes import report_bp

app.register_blueprint(quiz_bp)
app.register_blueprint(update_bp)
app.register_blueprint(report_bp)

# --- Optional: A simple root endpoint to confirm the server is running ---
@app.route('/')
def index():
    return jsonify({"status": "Server is running"})

if __name__ == '__main__':
    get_word_to_level_map()  # Prime the cache on server start
    app.run(debug=True, port=5000)