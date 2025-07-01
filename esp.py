from flask import Flask, request, jsonify, Response
import datetime, os
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)
API_KEY = os.getenv("API_KEY", "ajebukola")
def auth(req): return req.headers.get("API-KEY") == API_KEY

# ───── Mongo (optional logging) ─────
username = os.getenv("DB_USERNAME","youngsmartcr7")
password = quote_plus(os.getenv("DB_PASSWORD","Arowosaye1125@"))
client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.gisdocx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

mdb=client ["Power_monitoring"]
col_log = mdb["device_log"]            # raw packets
col_cmd = mdb["command"]               # queued cmds (optional)

# ───── in‑memory maps ─────
latest_state = {}     # {"ESP32‑001":"ON"}
pending_cmd  = {}     # {"ESP32‑001":"OFF"}

# ───────────────────────────────────────────
#  ESP POSTS power or load state
#  body {device:"ESP32‑001", state:"ON"}   ← state, not command
# ───────────────────────────────────────────
@app.route("/device-state", methods=["POST"])
def device_state():
    if not auth(request): return jsonify(err="unauthorized"), 401

    data   = request.get_json() or {}
    dev    = data.get("device")
    state  = (data.get("state") or "").upper()     # << fixed key
    if not dev or state not in {"ON","OFF"}:
        return jsonify(err="bad payload"), 400

    latest_state[dev] = state

    # optional history log
    data["timestamp"] = datetime.datetime.now()
    col_log.insert_one(data)

    return jsonify(ok="logged"), 200

# ───────────────────────────────────────────
#  Front‑end polls current snapshot
# ───────────────────────────────────────────
@app.route("/device-state/<device>", methods=["GET"])
def get_state(device):
    return jsonify(state = latest_state.get(device)), 200

# ───────────────────────────────────────────
#  Front‑end queues ON or OFF command
#  body {device:"ESP32‑001", command:"OFF"}
# ───────────────────────────────────────────
@app.route("/send-command", methods=["POST"])
def send_command():
    data = request.get_json() or {}
    dev  = data.get("device")
    cmd  = (data.get("command") or "").upper()
    if not dev or cmd not in {"ON","OFF"}:
        return jsonify(err="bad payload"), 400

    # ignore duplicates
    if latest_state.get(dev) == cmd:
        return jsonify(status="noop"), 200

    pending_cmd[dev] = cmd
    col_cmd.insert_one({"device":dev,"command":cmd,"ts":datetime.datetime.now()})
    return jsonify(status="queued"), 200

# ───────────────────────────────────────────
#  ESP polls for command  (plain text)
# ───────────────────────────────────────────
@app.route("/device-command/<device>", methods=["GET"])
def device_command(device):
    if not auth(request): return jsonify(err="unauthorized"), 401
    cmd = pending_cmd.pop(device, None)
    if cmd:
        return Response(cmd, mimetype="text/plain")
    return Response(status=204)        # << fixed (204 No Content)

# ───────────────────────────────────────────
#  Catch‑all log (still useful)
# ───────────────────────────────────────────
@app.route("/esp32-data", methods=["POST"])
def receive_data():
    if not auth(request): return jsonify(err="unauthorized"), 401
    data = request.get_json() or {}
    data["timestamp"] = datetime.datetime.now()
    col_log.insert_one(data)
    print("Data logged:", data)
    return jsonify(msg="saved"), 200

# ───────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
