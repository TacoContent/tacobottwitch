import requests
import json
import traceback
import typing
class DiscordWebhook():
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, content: typing.Union[str, None] = None, embeds=None):
        try:

            data = {}
            if content is not None:
                data['content'] = content
            if embeds is not None:
                data['embeds'] = embeds
            data['tts'] = False

            r = requests.post(self.webhook_url, data=data)
            if r.status_code != 200 and r.status_code != 204:
                print("Error sending webhook: " + str(r.status_code))
        except Exception as ex:
            print(ex)
            traceback.print_exc()
