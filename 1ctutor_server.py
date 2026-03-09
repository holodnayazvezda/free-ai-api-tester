import base64
import json
import threading
import uuid

import google.generativeai as genai
from flask import Flask, request, make_response, jsonify

from config import GEMINI_API_KEY

app = Flask(__name__)
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-pro-preview"

chat_sessions = {}
tasks = {}


def _decode_request() -> dict | None:
    raw = request.cookies.get("_sess", "")
    if not raw:
        return None
    try:
        return json.loads(base64.b64decode(raw))
    except Exception:
        return None


def _encode_response(data: dict, status_code: int = 200):
    payload = json.dumps(data, ensure_ascii=False)
    encoded = base64.b64encode(payload.encode()).decode()
    return make_response(jsonify({"cache": encoded}), status_code)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Server Error: {e}")
    return _encode_response({
        "status": "error",
        "error_type": type(e).__name__,
        "message": str(e),
    }, 500)


def get_chat_session(session_id):
    if session_id not in chat_sessions:
        model = genai.GenerativeModel(MODEL_NAME)
        chat_sessions[session_id] = model.start_chat(history=[])
    return chat_sessions[session_id]


def process_request(task_id, session_id, user_message):
    try:
        chat_session = get_chat_session(session_id)
        response = chat_session.send_message(user_message)
        tasks[task_id] = {"status": "completed", "result": response.text}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}


@app.route('/sync', methods=['POST'])
def sync():
    data = _decode_request()
    if data is None:
        return _encode_response({"status": "error", "message": "Bad request"}, 400)

    user_message = data.get('message')
    session_id = data.get('session_id')

    if not user_message:
        return _encode_response({"status": "error", "message": "No message"}, 400)

    if not session_id:
        session_id = str(uuid.uuid4())

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}

    thread = threading.Thread(
        target=process_request,
        args=(task_id, session_id, user_message),
    )
    thread.start()

    return _encode_response({
        "status": "queued",
        "task_id": task_id,
        "session_id": session_id,
    })


@app.route('/cache/<task_id>', methods=['GET'])
def get_cache(task_id):
    task = tasks.get(task_id)
    if not task:
        return _encode_response({"status": "error", "message": "Not found"}, 404)
    return _encode_response(task)



@app.route('/drop', methods=['POST'])
def drop_session():
    data = _decode_request()
    if data is None:
        return _encode_response({"status": "error"}, 400)

    session_id = data.get('session_id')
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return _encode_response({"status": "success"})
    return _encode_response({"status": "warning", "message": "Not found"}, 404)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=2027, debug=True)
