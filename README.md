# free-ai-api-tester

Тестовый HTTP-сервис для диалога с Gemini и консольный клиент. Запросы выполняются в фоновых потоках, результат получается по идентификатору задачи. Сессии и задачи хранятся в памяти.

## Запуск

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install flask google-generativeai requests
python server.py
```

Укажите собственный `GEMINI_API_KEY` в `config.py`. Выбранная модель задаётся константой `MODEL_NAME` в сервере и должна быть доступна для вашего ключа.

`server.py` слушает порт `2026`:

- `POST /chat` — JSON с `message` и необязательным `session_id`; возвращает `task_id`.
- `GET /result/<task_id>` — состояние задачи и ответ.
- `POST /reset` — сброс контекста по `session_id`.

Для `python client.py` задайте `SERVER_URL`, например `http://localhost:2026`. Команды клиента: `/reset`, `/exit`, `file-путь_к_файлу` для отправки текста файла.

`1ctutor_server.py` — отдельный вариант на порту `2027` с маршрутами `/sync`, `/cache/<task_id>`, `/drop` и передачей данных через Base64. Он использует другой протокол и не является прямой заменой `server.py` для этого клиента.
