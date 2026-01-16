from google import genai
from PIL import Image  # Импортируем библиотеку для работы с картинками
import sys
import os

from google.genai import types

# Импорт ключа из вашего файла config.py
try:
    from config import GEMINI_API_KEY
except ImportError:
    print("Ошибка: файл config.py не найден или в нем нет GEMINI_API_KEY")
    sys.exit(1)

def run_chat():
    try:
        client = genai.Client(api_key=GEMINI_API_KEY,  http_options=types.HttpOptions(timeout=300000) )
        # Обратите внимание: убедитесь, что модель "gemini-3-flash-preview" доступна.
        # Если будет ошибка 404, попробуйте "gemini-2.0-flash-exp" или "gemini-1.5-flash"
        chat = client.chats.create(model="gemini-3-flash-preview")
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        return

    print("Чат с Gemini запущен!")
    print("Команды:")
    print(" - Просто текст: обычное общение")
    print(" - image-путь/к/файлу.jpg: отправить картинку")
    print(" - выход: завершить")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nВы: ").strip()

            if user_input.lower() in ['выход', 'exit', 'quit']:
                print("Завершение работы.")
                break

            if not user_input:
                continue

            message_payload = user_input # По умолчанию отправляем просто текст

            # --- БЛОК ОБРАБОТКИ ИЗОБРАЖЕНИЙ ---
            if user_input.startswith("image-"):
                image_path = user_input[6:].strip() # Убираем "image-"

                if os.path.exists(image_path):
                    try:
                        # 1. Загружаем изображение через Pillow
                        img = Image.open(image_path)

                        # 2. Спрашиваем у пользователя промпт к картинке
                        caption = input("Текст к изображению (нажмите Enter, чтобы отправить без текста): ").strip()

                        # 3. Формируем список для отправки: [Картинка, Текст]
                        # Если текста нет, отправляем просто [Картинка]
                        message_payload = [img, caption] if caption else [img]

                        print(f"Загружено изображение: {image_path}")
                    except Exception as img_err:
                        print(f"Ошибка чтения файла изображения: {img_err}")
                        continue
                else:
                    print(f"Файл не найден: {image_path}")
                    continue
            # ----------------------------------

            print("Gemini думает...", end="\r")

            # Отправка (принимает либо строку, либо список [img, str])
            response = chat.send_message(message=message_payload)

            # Очистка индикатора
            print(" " * 20, end="\r")

            print(f"Gemini: {response.text}")

        except ImportError as e:
            print(f"\nПроизошла ошибка API: {e}")

if __name__ == "__main__":
    run_chat()