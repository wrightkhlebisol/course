"""
Web dashboard for troubleshooting recommendations
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import requests
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
API_BASE_URL = "http://localhost:8000"

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/submit-incident', methods=['POST'])
def submit_incident():
    """Submit incident and get recommendations"""
    try:
        incident_data = request.json
        
        # Call recommendation API
        response = requests.post(
            f"{API_BASE_URL}/api/recommendations",
            json=incident_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to get recommendations"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on recommendations"""
    try:
        feedback_data = request.json
        
        response = requests.post(
            f"{API_BASE_URL}/api/feedback",
            json=feedback_data,
            timeout=10
        )
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/execute-solution', methods=['POST'])
def execute_solution():
    """Execute a solution and get execution results"""
    try:
        execution_data = request.json
        
        response = requests.post(
            f"{API_BASE_URL}/api/execute",
            json=execution_data,
            timeout=60  # Longer timeout for execution
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to execute solution"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
