import requests
import logging
from secrets_handler import VARIABLES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bot_logger")

class TelegramBot:
    def __init__(self, token):
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def send_request(self, method, data):
        url = self.base_url + method
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()  # Raise an error for bad status codes
            logger.info("Message sent successfully: %s", response)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Error sending message: %s", e)
            return "Failed Request to TG API"

    def send_message(self, chat_id, text):
        data = {'chat_id': chat_id, 'text': text}
        return self.send_request('sendMessage', data)

    def reply_message(self, chat_id, msg_id, text):
        data = {
            'chat_id': chat_id,
            'text': text,
            'reply_to_message_id': msg_id
        }
        return self.send_request('sendMessage', data)

    def send_photo(self, file_loc, caption, chat_id):
        with open(file_loc, "rb") as image_file:
            # Prepare data for the POST request (multipart form data)
            files = {
                "chat_id": (None, chat_id),
                "photo": (image_file.name, image_file, "image/jpeg"),
                "caption": (None, caption)
            }

            return requests.post(self.base_url + 'sendPhoto', files=files)


bot = TelegramBot(VARIABLES['BOT_TOKEN'])
