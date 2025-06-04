import base64
import requests


class OpenRouterAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url_default = 'https://openrouter.ai/api/v1/chat/completions'

    def message(self, prompt, model="deepseek/deepseek-r1-0528:free", photo=None):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}"
                        },
                    ]
                }
            ],
        }
        if photo is not None:
            data["messages"][0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{self._encode_image_to_base64(photo)}"
                }
            })

        response = requests.post(self.api_url_default, json=data, headers=headers)

        if response.status_code != 200:
            return f"error(!): {response.status_code}"

        print(response.json())
        return response.json()['choices'][0]['message']["content"]

    def _encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
