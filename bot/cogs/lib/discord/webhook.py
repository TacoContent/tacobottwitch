import requests
import json
import traceback
import typing
class DiscordWebhook():
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, content: typing.Union[str, None] = None, embeds=None):
        try:
            r = requests.post(self.webhook_url, data={ 'content': content, 'embeds': embeds, 'tts': False })
            if r.status_code != 200 and r.status_code != 204:
                print("Error sending webhook: " + str(r.status_code))
        except Exception as ex:
            print(ex)
            traceback.print_exc()
