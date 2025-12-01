import random

AIML_KEYS = [
    "REMOVED_SECRET",
    "REMOVED_SECRET",
    "REMOVED_SECRET",
    "REMOVED_SECRET",
    "REMOVED_SECRET"
]

def get_random_key():
    return random.choice(AIML_KEYS)

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def ask_aimlapi():
    from openai import OpenAI
    import requests

    client = OpenAI(
        api_key=get_random_key(),
        base_url="https://api.aimlapi.com/v1",
    )

    model = "gpt-4o"

    messages = [
        {
            "role": "system",
            "content": (
                "Ты отличный помощник по олимпиадному программированию. "
                "Ты получаешь условие задачи и даёшь максимально оптимальное решение на Python. "
                "Отдавай полный код."
            )
        }
    ]

    while True:
        users_request = input("> ")
        if users_request == "exit":
            break

        if "img" in users_request:
            try:
                filename, caption = users_request.split("-")[1:]
                base64_data = encode_image_to_base64(filename)

                api_key = get_random_key()

                url = "https://api.aimlapi.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "gpt-4o",
                    "messages": [
                        *messages,
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": caption},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_data}"
                                    }
                                }
                            ]
                        }
                    ]
                }

                response = requests.post(url, headers=headers, json=payload)
                r = response.json()
                response_text = r["choices"][0]["message"]["content"]
                print(response_text)

                messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                print("Image error:", e)

        else:
            try:
                if users_request == "f":
                    with open("data.txt", "r") as f:
                        users_request = f.read()

                messages.append({"role": "user", "content": users_request})

                client = OpenAI(
                    api_key=get_random_key(),
                    base_url="https://api.aimlapi.com/v1",
                )

                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )

                response_text = completion.choices[0].message.content
                print(response_text)

                if response_text:
                    messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                print("Error:", e)

ask_aimlapi()
