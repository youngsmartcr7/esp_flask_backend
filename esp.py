from flask import Flask, request, jsonify
import datetime
from pymongo import MongoClient
from urllib.parse import quote_plus
import os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY", "ajebukola")

# MongoDB credentials from environment
username = os.getenv("DB_USERNAME","youngsmartcr7")
password = quote_plus(os.getenv("DB_PASSWORD", "Arowosaye1125@"))
client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.gisdocx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

db = client["Power_monitoring"]
device_data_col = db["device_data"]
command_col = db["command"]

def check_api_key(req):
    key = req.headers.get("API-KEY")
    return key == API_KEY

@app.route('/esp32-data', methods=['POST'])
def receive_data():
    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    data['timestamp'] = datetime.datetime.now()
    device_data_col.insert_one(data)
    print("Data logged:", data)
    return jsonify({"message": "Data saved to DB"}), 200

last_command = {"device": None, "command": None}

@app.route('/send-command', methods=['POST'])
def send_command():
    data = request.get_json()
    device = data.get('device')
    command = data.get('command')

    if not device or not command:
        return jsonify({"status": "error", "message": "Missing device or command"}), 400

    last_command["device"] = device
    last_command["command"] = command
    return jsonify({"status": "success", "message": f"Command '{command}' sent to {device}."}), 200

@app.route('/device-command', methods=['GET'])
def device_command():
    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    command_to_send = last_command.copy()
    last_command["command"] = None
    return jsonify(command_to_send)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
