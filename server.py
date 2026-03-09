import threading
import uuid

import google.generativeai as genai
from flask import Flask, request, jsonify, make_response

from config import GEMINI_API_KEY

app = Flask(__name__)
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-pro-preview"

chat_sessions = {}

# Хранилище статусов задач
# Структура: { "task_id": { "status": "processing"|"completed"|"failed", "result": "...", "error": "..." } }
tasks = {}

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Server Error: {e}")
    return make_response(jsonify({
        "status": "error",
        "error_type": type(e).__name__,
        "message": str(e)
    }), 500)

def get_chat_session(session_id):
    """Возвращает или создает сессию (синхронно)."""
    if session_id not in chat_sessions:
        model = genai.GenerativeModel(MODEL_NAME)
        chat_sessions[session_id] = model.start_chat(history=[])
        print(f"[INFO] Создана новая сессия: {session_id}")
    return chat_sessions[session_id]

def process_gemini_request(task_id, session_id, user_message):
    """
    Функция, которая будет работать в фоновом потоке.
    Она делает долгий запрос к API и обновляет статус задачи.
    """
    print(f"[TASK] Начало обработки задачи {task_id}")
    try:
        chat_session = get_chat_session(session_id)
        response = chat_session.send_message(user_message)

        tasks[task_id] = {
            "status": "completed",
            "result": response.text
        }
        print(f"[TASK] Задача {task_id} завершена успешно.")

    except Exception as e:
        # Сохраняем ошибку
        tasks[task_id] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"[TASK] Задача {task_id} упала с ошибкой: {e}")

# --- Эндпоинты ---

@app.route('/chat', methods=['POST'])
def chat():
    """
    Принимает запрос, создает задачу и сразу возвращает ID.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "JSON required"}), 400
    data = request.get_json()
    user_message = data.get('message')
    session_id = data.get('session_id')

    if not user_message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    if not session_id:
        session_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    thread = threading.Thread(
        target=process_gemini_request,
        args=(task_id, session_id, user_message)
    )
    thread.start()
    return jsonify({
        "status": "queued",
        "task_id": task_id,
        "session_id": session_id,
        "message": "Запрос принят в обработку. Ожидайте результата."
    })

@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    """
    Позволяет клиенту проверить статус задачи по ID.
    """
    task = tasks.get(task_id)

    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404

    # Возвращаем текущее состояние задачи
    return jsonify(task)

@app.route('/reset', methods=['POST'])
def reset_context():
    if not request.is_json:
        return jsonify({"status": "error"}), 400
    data = request.get_json()
    session_id = data.get('session_id')

    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return jsonify({"status": "success", "message": "Context reset"})
    else:
        return jsonify({"status": "warning", "message": "Session not found"}), 404

if __name__ == "__main__":
    print(f"Сервер запущен на порту 2026. Асинхронный режим.")
    app.run(host='0.0.0.0', port=2026, debug=True)