OPENROUTER = [
    "REMOVED_SECRET",
    "REMOVED_SECRET",
    "REMOVED_SECRET"
]

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def ask_openrouter():
    from openai import OpenAI
    import requests

    client = OpenAI(
        api_key=OPENROUTER[0],
        base_url="https://openrouter.ai/api/v1"
    )
    model = 'gpt-5'

    messages = [
        {"role": "system", "content": "ты очень хороший помошник, который выполняет важную задачу: решает задачи по олимпиадному программированию. тебе отправляют условия задачи, а твоя задача - написаь код - решение задачи. максимально эффективный и правильный. Выложись на максимум, за свою работу ту получищь много долларов"}
    ]
    while True:
        users_request = input("> ")
        if users_request == "exit":
            break

        if 'img' in users_request:
            try:
                filename, caption = users_request.split('-')[1:]
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {OPENROUTER[0]}",
                    "Content-Type": "application/json"
                }
                data_url = f"data:image/jpeg;base64,{encode_image_to_base64(filename)}"
                messages.append({"role": "user",
                                "content": [
                                    { "type": "text", "text": caption },
                                    { "type": "image_url", "image_url": {"url": data_url} }
                                ]})
                payload = {"model": "google/gemini-2.0-flash-001", "messages": messages}
                response = requests.post(url, headers=headers, json=payload)
                response_data = response.json()
                response_text = response_data['choices'][0]['message']['content']
                print(response_text)
                messages.append({'role': 'assistant', 'content': response_text})
            except Exception as e:
                print(e)
        else:
            try:
                if users_request == 'f':
                    f = open('data.txt', 'w')
                    users_request = f.read()
                    f.close()
                messages.append(
                    {"role": "user", "content": users_request}
                )
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                response_text = completion.choices[0].message.content
                print(response_text)
                if response_text:
                    messages.append({'role': 'assistant', 'content': response_text})
            except Exception as e:
                print(e)


ask_openrouter()
