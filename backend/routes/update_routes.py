from flask import Blueprint, jsonify, request
import data_manager
from services import quiz_service # <-- IMPORT THE NEW SERVICE

update_bp = Blueprint('update_bp', __name__)

@update_bp.route('/api/update', methods=['POST'])
def update_words():
    """
    A thin controller that handles the HTTP request and delegates
    the business logic to the quiz_service.
    """
    data = request.json
    results = data.get('results', [])
    level = data.get('level') # Still useful for validation
    
    # 1. Basic validation
    if not level or level not in data_manager.LEVELS:
        return jsonify({"error": "Invalid or missing level"}), 400
    
    if not results:
        return jsonify({"status": "success", "message": "No results to process."})

    # 2. Delegate to the service layer
    try:
        quiz_service.process_quiz_results(results)
        return jsonify({"status": "success", "message": f"Updated {len(results)} words."})
    except Exception as e:
        # Basic error handling for any issues in the service layer
        print(f"ERROR: An error occurred during quiz processing: {e}")
        return jsonify({"error": "An internal error occurred while processing the results."}), 500