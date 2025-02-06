from flask import Flask, request, jsonify
import time
import os
import json
from sqlDB import SQLiteDB
from dotenv import load_dotenv

load_dotenv()

db_name = os.getenv("DATABASE")
db = SQLiteDB(db_path=db_name)
app = Flask(__name__)

def log_request(endpoint):
    """Logs incoming request details."""
    print(f"Received request on {endpoint} - Method: {request.method}")
    print(f"Data: {request.json}")

@app.route('/')
def hello():
    time.sleep(10)
    return jsonify({"message": "hii"})

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

@app.route('/file-path', methods=['GET'])
def get_file_path():
    log_request('/file-path')
    time.sleep(10)
    projectpath = request.args.get('projectpath', default='false', type=str)
    if projectpath.lower() == 'true':
        project_folder_path = os.path.abspath(os.getcwd())
        return jsonify({'path': project_folder_path})
    else:
        dcc_file_path = os.path.abspath('*.dcc')
        return jsonify({'path': dcc_file_path})

@app.route('/add-item', methods=['POST'])
def add_item_to_db():
    log_request('/add-item')
    time.sleep(10)
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'quantity' not in data:
            return jsonify({'status': 400, 'message': 'Missing required fields: name and quantity'}), 400
        if isinstance(data['quantity'], dict):
            data['quantity'] = json.dumps(data['quantity'])
        status, message = db.add_item(data)
        return jsonify({'status': status, 'message': message}), status
    except json.JSONDecodeError:
        return jsonify({'status': 400, 'message': 'Invalid JSON format'}), 400
    except Exception:
        return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500

@app.route('/get-all-items', methods=['GET'])
def get_items():
    log_request('/get-all-items')
    time.sleep(10)
    try:
        res = db.get_all_items()
        if res:
            return jsonify({'message': 'All items fetched successfully', 'res': res}), 200
        return jsonify({'message': 'Could not fetch all the items'}), 500
    except Exception:
        return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500

@app.route('/remove-item', methods=['DELETE'])
def delete_item():
    log_request('/remove-item')
    time.sleep(10)
    try:
        data = request.get_json()
        status, message = db.remove_item(data)
        return jsonify({'status': status, 'message': message}), status
    except json.JSONDecodeError:
        return jsonify({'status': 400, 'message': 'Invalid JSON format'}), 400
    except Exception:
        return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500

@app.route('/update-quantity', methods=['PUT'])
def update():
    log_request('/update-quantity')
    time.sleep(10)
    try:
        data = request.get_json()
        status, message = db.update_qty(data)
        return jsonify({'status': status, 'message': message}), status
    except json.JSONDecodeError:
        return jsonify({'status': 400, 'message': 'Invalid JSON format'}), 400
    except Exception:
        return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500


# now we ned to define tigger to get all the logs of delete / update including provded timestamp
@app.route('get-all-logs',methods=['GET'])
def get_all_logs():
    try:
        log_request('/file-path')
        time.sleep(10)
        delete = request.args.get('delete', default='false', type=str)

        data = request.get_json()
        if delete.tolower() == 'true':
            #itsabout delete
            status , data_ = db.get_all_delete_logs(data)
            return status,data_
        else:
            #its all about update
            status , data_ = db.get_all_update_logs(data)
            return status,data_

    except Exception as e:
        print("Error in getting logs: ",str(e))


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": f"{error}"}), 404  

flask_host = os.getenv("FLASK_HOST", "127.0.0.1")
flask_port = int(os.getenv("FLASK_PORT", "8000"))

if __name__ == '__main__':
    app.run(host=flask_host, port=flask_port, debug=True)
