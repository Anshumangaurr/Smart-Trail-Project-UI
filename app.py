import sys
import os
# Ensure the directory containing this script is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, Response, jsonify, request
try:
    from camera import VideoCamera
except ImportError as e:
    # If the camera module or dependencies are missing, we can still run
    # the web app; camera-related endpoints will return errors gracefully.
    print(f"Error importing VideoCamera: {e}")
    VideoCamera = None

app = Flask(__name__)

# Global state for the "Robot"
robot_state = {
    "status": "Idle",  # Idle, Follow, Return
    "battery": 98.0,
    "last_command": "None"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rent')
def rent():
    return render_template('rent.html')

@app.route('/activate')
def activate():
    return render_template('activate.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/end_ride')
def end_ride():
    return render_template('end_ride.html')

@app.route('/api/toggle_camera', methods=['POST'])
def toggle_camera():
    """
    Toggle or explicitly set the camera running state.
    Request body options (JSON):
      - {"run": true}  -> force camera ON
      - {"run": false} -> force camera OFF / privacy mode
      - {} or no body  -> toggle current state
    """
    cam = get_camera()
    if cam is None:
        return jsonify({"status": "error", "message": "Camera unavailable"}), 500

    data = request.get_json(silent=True) or {}

    if "run" in data:
        # Explicitly set the running state
        should_run = bool(data["run"])
    else:
        # No explicit flag provided, just toggle based on current state
        should_run = not getattr(cam, "is_running", True)

    cam.set_running(should_run)
    return jsonify({"status": "success", "running": should_run})

# We need a proper singleton for the camera to toggle state effectively
global_camera = None

def get_camera():
    global global_camera
    if global_camera is None:
        if VideoCamera:
            global_camera = VideoCamera()
    return global_camera

@app.route('/video_feed')
def video_feed():
    cam = get_camera()
    if cam is None:
        return "Camera error", 500
    return Response(gen(cam), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera_control', methods=['POST'])
def camera_control():
    cam = get_camera()
    if cam is None:
        return jsonify({"status": "error", "message": "Camera unavailable"}), 500

    data = request.get_json(silent=True) or {}
    should_run = bool(data.get('on', True))
    cam.set_running(should_run)
    return jsonify({"status": "updated", "running": should_run})

@app.route('/api/control', methods=['POST'])
def control():
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'follow':
            robot_state['status'] = 'Following'
        elif action == 'stop':
            robot_state['status'] = 'Stopped'
        elif action == 'return':
            robot_state['status'] = 'Returning'
        
        robot_state['last_command'] = action
        return jsonify({"status": "success", "robot_state": robot_state})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/status')
def status():
    # Simulate battery drain
    if robot_state['status'] == 'Following':
        robot_state['battery'] = max(0.0, float(robot_state['battery']) - 0.01)
        
    return jsonify(robot_state)


@app.route('/api/health')
def health():
    """
    Simple health check endpoint for debugging.
    Returns basic info about server, robot, and camera availability.
    """
    cam_available = get_camera() is not None
    return jsonify(
        {
            "status": "ok",
            "robot_state": robot_state,
            "camera_available": cam_available,
        }
    )

if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible to other devices if needed, but verify firewall.
    # debug=True allows hot reloading which is useful for development.
    print("Starting SmartTrail Server...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host='0.0.0.0', port=5000, debug=True)
