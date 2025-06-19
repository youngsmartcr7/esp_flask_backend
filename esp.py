from flask import Flask, request, jsonify
import datetime
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)

API_KEY = "ajebukola"

#Mongo setup 
username = "youngsmartcr7"
password = quote_plus("Arowosaye1125@")
client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.gisdocx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["Power_monitoring"]
device_data_col = db["device_data"]
command_col = db["command"]

# autentication setup 
def check_api_key(req):
    key = req.headers.get("API-KEY")
    if key != API_KEY:
        return False
    return True

@app.route('/esp32-data', methods= ['POST'])
def receive_data():
    if not check_api_key(request):
        return jsonify({"erroe": "unauthorized"}), 401

    data= request.get_json()
    data['timestamp'] = datetime.datetime.now()

    '''
    #log to file with timestamp
    with open("esp32_data_log.txt", "a") as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {data}\n")

    print("Receive data: ", data)
    return jsonify({"message": " data received and logged succesfully"}), 200
    '''
    #save to mongo
    device_data_col.insert_one(data)

    print("Data logged:", data)
    return jsonify({"message": "Data saved to DB"}), 200

# Store the last command sent by the esp32
last_command = {"device": None, "command": None}

@app.route('/send-command', methods=['POST'])
def send_command():
    data = request.get_json()
    device = data.get('device')
    command = data.get('command')

    if not device or not command:
        return jsonify({"status": "error", "message": f" missing '{command}' sent to {device}."}), 400
    
    #upsert command into database
    last_command["device"] = device
    last_command["command"] = command
    #command_col.update_one(
    #    {"device": device}, {"$set": {"command": command, "timestamp": datetime.datetime.now()}}, upsert=True
    #)

    return jsonify({"status": "success", "message": f"Command '{command}' sent to {device}."}), 200

@app.route ('/device-command', methods=['GET'])
def device_command():
    #return jsonify(last_command)
    if not check_api_key(request):
      return jsonify({"error": "Unauthorized"}), 401

    command_to_send = last_command.copy()
    #Reset the command after it is fetched
    last_command["command"] = None
    return jsonify(command_to_send)

if __name__ == '__main__':
    from os import environ
    port=int(environ.get("PORT", 5000))
    app.run(host= '0.0.0.0', port=port)
