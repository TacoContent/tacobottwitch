import traceback
import typing

import requests


class TacobotWebhook:
    def __init__(self, webhook_url: str, auth_token: typing.Optional[str]) -> None:
        self.webhook_url = webhook_url
        self.auth_token = auth_token

    def send_payload(self, payload: dict) -> None:
        try:

            if self.auth_token is not None:
                headers = {"X-TACOBOT-TOKEN": f"{self.auth_token}"}

            r = requests.post(self.webhook_url, headers=headers, json=payload)
            if r.status_code != 200 and r.status_code != 204:
                print("Error sending webhook: " + str(r.status_code))
                print(r.text)
            else:
                print("Webhook sent successfully")

            return r.json()

        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None

    def send(self, **kwargs) -> None:
        try:
            data = {}

            for key, value in kwargs.items():
                if value is not None:
                    data[key] = value

            return self.send_payload(data)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
