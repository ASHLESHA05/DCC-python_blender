from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

def log_request(endpoint):
    """Logs incoming request details."""
    print(f"Received request on {endpoint} - Method: {request.method}")
    print(f"Data: {request.json}")

@app.route('/transform', methods=['POST'])
def receive_transform():
    log_request('/transform')
    time.sleep(10)  
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400 
    return jsonify({"message": "Transform received successfully!"}), 200  

@app.route('/scale', methods=['POST'])
def receive_scale():
    log_request('/scale')
    time.sleep(10)
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    return jsonify({"message": "Scale received successfully!"}), 200

@app.route('/rotate', methods=['POST'])
def receive_rotation():
    log_request('/rotate')
    time.sleep(10)

    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    return jsonify({"message": "Rotation received successfully!"}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": f"{error}"}), 404  

# Get environment variables or use defaults
flask_host = os.getenv("FLASK_HOST", "127.0.0.1")  # Default to localhost
flask_port = int(os.getenv("FLASK_PORT", "8000"))   # Default to port 8000

print(f"env: {flask_host} | {flask_port}")

if __name__ == '__main__':
    app.run(host=flask_host, port=flask_port, debug=True)

