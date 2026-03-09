import os
import time
import uuid

import requests

SERVER_URL = "https://crushvpn.ru/ai"

def print_bot(text):
    print(f"Gem: {text}")

def print_sys(text):
    print(f"[SYSTEM]: {text}")

def print_error(text):
    print(f"[ERROR]: {text}")

def reset_session(session_id):
    try:
        response = requests.post(f"{SERVER_URL}/reset", json={"session_id": session_id})
        if response.status_code == 200:
            print_sys("сброшено")
        else:
            print_error(f"reset: {response.status_code}")
    except Exception as e:
        print_error(f"Ошибка: {e}")

def wait_for_result(task_id):
    print_sys("Ожидание...")
    while True:
        try:
            response = requests.get(f"{SERVER_URL}/result/{task_id}")

            if response.status_code != 200:
                print(f"\n[ERROR] Не удалось получить статус задачи (Code {response.status_code})")
                return

            data = response.json()
            status = data.get("status")

            if status == "completed":
                print(" Готово!")
                print("-" * 20)
                print_bot(data.get("result"))
                print("-" * 20)
                break

            elif status == "failed":
                print(" Ошибка!")
                print_error(f"Сервер сообщил об ошибке: {data.get('error')}")
                break

            elif status == "processing":
                print(".", end="", flush=True)
                time.sleep(2)

            else:
                print(f"\n[WARN] Неизвестный статус: {status}")
                break

        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Потеряно соединение")
            break
        except Exception as e:
            print(f"\n[ERROR] Ошибка клиента: {e}")
            break

def send_message(session_id, message):
    payload = {
        "session_id": session_id,
        "message": message
    }

    try:
        response = requests.post(f"{SERVER_URL}/chat", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            wait_for_result(task_id)
        else:
            print_error(f"Не удалось создать задачу. Code: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print_error("Нет соединения с сервером.")
    except Exception as e:
        print_error(f"Ошибка: {e}")

def read_file_content(filepath):
    if not os.path.exists(filepath):
        print_error(f"Файл не найден: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print_sys(f"Файл прочитан: {filepath}")
        return content
    except Exception as e:
        print_error(f"Ошибка чтения: {e}")
        return None

def main():
    session_id = str(uuid.uuid4())
    print(f"Server: {SERVER_URL}")
    print(f"Session ID: {session_id}")
    print("-" * 30)
    while True:
        try:
            user_input = input("Вы: ").strip()
            if not user_input: continue
            if user_input.lower() in ['/exit', 'exit']:
                break
            if user_input.lower() == '/reset':
                reset_session(session_id)
                continue
            message = user_input
            if user_input.startswith("file-"):
                path = user_input[5:].strip()
                content = read_file_content(path)
                if content:
                    message = content
                else:
                    continue
            send_message(session_id, message)

        except KeyboardInterrupt:
            print("\nВыход...")
            break

if __name__ == "__main__":
    main()