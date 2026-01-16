from flask import Flask, request, jsonify, make_response
import google.generativeai as genai
import uuid
from config import GEMINI_API_KEY

app = Flask(__name__)

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3-pro-preview"


chat_sessions = {}


@app.errorhandler(Exception)
def handle_exception(e):
    """
    Перехватывает любые ошибки сервера и возвращает их в JSON формате.
    """
    app.logger.error(f"Server Error: {e}")
    return make_response(jsonify({
        "status": "error",
        "error_type": type(e).__name__,
        "message": str(e)
    }), 500)


def get_chat_session(session_id):
    """
    Возвращает объект чата или создает новый.
    """
    if session_id not in chat_sessions:
        model = genai.GenerativeModel(MODEL_NAME)
        chat_sessions[session_id] = model.start_chat(history=[])
        print(f"[INFO] Создана новая сессия: {session_id}")
    return chat_sessions[session_id]


# --- Эндпоинты ---

@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type должен быть application/json"}), 400

    data = request.get_json()
    user_message = data.get('message')
    session_id = data.get('session_id')

    if not user_message:
        return jsonify({"status": "error", "message": "Поле 'message' обязательно"}), 400

    if not session_id:
        session_id = str(uuid.uuid4())
    try:
        chat_session = get_chat_session(session_id)
        response = chat_session.send_message(user_message)

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "response": response.text
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Ошибка при запросе к Gemini API: {str(e)}"
        }), 500


@app.route('/reset', methods=['POST'])
def reset_context():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type должен быть application/json"}), 400

    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"status": "error", "message": "Поле 'session_id' обязательно для сброса"}), 400

    if session_id in chat_sessions:
        del chat_sessions[session_id]
        print(f"[INFO] Сессия сброшена: {session_id}")
        return jsonify({"status": "success", "message": "Контекст диалога успешно сброшен"})
    else:
        return jsonify({"status": "warning", "message": "Сессия не найдена (возможно, уже была удалена)"}), 404


if __name__ == "__main__":
    print(f"Сервер запущен. Модель: {MODEL_NAME}")
    app.run(host='0.0.0.0', port=2026, debug=True)