import os
import sys
import base64
import json
import httpx # Используем httpx напрямую для контроля протокола
from PIL import Image
from io import BytesIO

# Импорт ключа
try:
    from config import GEMINI_API_KEY
except ImportError:
    print("Ошибка: файл config.py не найден или в нем нет GEMINI_API_KEY")
    sys.exit(1)

# === НАСТРОЙКИ ===
MODEL_NAME = "gemini-3-pro-preview" # Или gemini-2.0-flash-exp
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:streamGenerateContent?key={GEMINI_API_KEY}"

def encode_image(image_path):
    """Кодирует картинку в base64 для отправки"""
    try:
        with Image.open(image_path) as img:
            # Конвертируем в JPEG (если png) и в байты
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_bytes = buffered.getvalue()
            return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")
        return None

def run_chat():
    print(f"Запуск чата с моделью {MODEL_NAME} (HTTP/2 Force Mode)")
    print("Команды те же: текст или image-путь/к/файлу.jpg")
    print("-" * 50)

    # История чата (чтобы нейросеть помнила контекст)
    chat_history = []

    # Создаем клиент с принудительным HTTP/2 и без тайм-аута
    # http2=True - это ГЛАВНОЕ лекарство от разрывов связи
    client = httpx.Client(http2=True, timeout=None)

    while True:
        try:
            user_input = input("\nВы: ").strip()

            if user_input.lower() in ['выход', 'exit', 'quit']:
                print("Завершение работы.")
                break

            if not user_input:
                continue

            # Подготовка контента пользователя
            user_parts = []

            # --- БЛОК ОБРАБОТКИ ИЗОБРАЖЕНИЙ ---
            if user_input.startswith("image-"):
                image_path = user_input[6:].strip()
                if os.path.exists(image_path):
                    b64_image = encode_image(image_path)
                    if b64_image:
                        # Добавляем картинку
                        user_parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_image
                            }
                        })

                        caption = input("Текст к изображению: ").strip()
                        if caption:
                            user_parts.append({"text": caption})
                        print(f"Изображение {image_path} прикреплено.")
                    else:
                        continue
                else:
                    print(f"Файл не найден: {image_path}")
                    continue
            else:
                # Просто текст
                user_parts.append({"text": user_input})
            # ----------------------------------

            # Формируем тело запроса с учетом истории
            # Добавляем текущее сообщение в историю (пока локально)
            current_message = {"role": "user", "parts": user_parts}
            request_contents = chat_history + [current_message]

            payload = {
                "contents": request_contents
            }

            print("Gemini думает (HTTP/2)...", end="\r")

            full_response_text = ""

            # Отправляем запрос вручную
            # stream=True позволяет читать ответ по кусочкам
            try:
                with client.stream("POST", API_URL, json=payload, headers={"Content-Type": "application/json"}) as response:

                    # Проверяем, не вернул ли сервер ошибку сразу (например 404 или 400)
                    if response.status_code != 200:
                        print(f"\nОшибка сервера: {response.status_code}")
                        print(response.read().decode())
                        continue

                    print(" " * 30, end="\r") # Чистим строку статуса

                    # Читаем SSE (Server-Sent Events)
                    for line in response.iter_lines():
                        if not line: continue

                        # Формат SSE приходит как "data: {...json...}"
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith("data:"):
                            json_str = decoded_line[5:].strip() # Убираем "data: "
                            try:
                                chunk_data = json.loads(json_str)
                                # Извлекаем текст из кандидата
                                candidates = chunk_data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        text_chunk = part.get("text", "")
                                        if text_chunk:
                                            print(text_chunk, end="", flush=True)
                                            full_response_text += text_chunk
                            except json.JSONDecodeError:
                                pass

                print() # Перенос строки в конце

                # Если ответ получен, сохраняем пару (вопрос-ответ) в историю
                if full_response_text:
                    chat_history.append(current_message)
                    chat_history.append({
                        "role": "model",
                        "parts": [{"text": full_response_text}]
                    })

            except httpx.RemoteProtocolError:
                print("\n[Сбой] Сервер разорвал соединение, но HTTP/2 должен был помочь.")
            except Exception as e:
                print(f"\nОшибка сети: {e}")

        except KeyboardInterrupt:
            print("\nВыход.")
            break
        except Exception as global_e:
            print(f"\nКритическая ошибка: {global_e}")

if __name__ == "__main__":
    run_chat()