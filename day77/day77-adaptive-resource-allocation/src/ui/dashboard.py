from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'adaptive-resource-allocation-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global allocator instance
allocator = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    if allocator:
        return jsonify(allocator.get_system_status())
    else:
        return jsonify({'error': 'Allocator not initialized'}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get detailed metrics"""
    if allocator:
        status = allocator.get_system_status()
        return jsonify({
            'current': status['current_metrics'],
            'summary': status['metrics_summary'],
            'resources': status['resource_allocation']
        })
    else:
        return jsonify({'error': 'Allocator not initialized'}), 500

@app.route('/api/scaling', methods=['POST'])
def trigger_scaling():
    """Manually trigger scaling action"""
    if not allocator:
        return jsonify({'error': 'Allocator not initialized'}), 500
        
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['scale_up', 'scale_down']:
        return jsonify({'error': 'Invalid action'}), 400
        
    success = allocator.force_scaling_action(action)
    return jsonify({'success': success, 'action': action})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to Adaptive Resource Allocation Dashboard'})

@socketio.on('request_update')
def handle_request_update():
    """Handle real-time update request"""
    if allocator:
        status = allocator.get_system_status()
        emit('status_update', status)

def start_real_time_updates():
    """Send periodic updates to connected clients"""
    def update_loop():
        while True:
            if allocator:
                try:
                    status = allocator.get_system_status()
                    socketio.emit('status_update', status)
                except Exception as e:
                    print(f"Error sending update: {e}")
            time.sleep(5)  # Update every 5 seconds
            
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()

def set_allocator(allocator_instance):
    """Set the allocator instance for the dashboard"""
    global allocator
    allocator = allocator_instance

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
