from os import path
import os
import json

from telegram.bot import bot, logger
from telegram.models import Message,CallbackQuery


from reception.bank import reply_for_utr
from reception.main import reception_api
from cook.main import get_all_balance

#Variable Declaration
module_dir = path.dirname(path.realpath(__file__))
templates_dir = path.join(module_dir, "templates")
ADMINS = ['1325461175','890642031','5722408084']

isAdmin = lambda x:str(x) in ADMINS

#Admin Report
def report_reception():
    data = reception_api.get_report()
    resp = '\n'
    for i in data.keys():
        resp += (f"Members {i}\n▶️ Today   :{int(data[i]['Today'])}"
                            f"\n▶️ Overall :{int(data[i]['Overall'])}\n\n")
    return resp

def report_balance():
    balance = get_all_balance()
    resp = ''
    for server,bal in balance.items():
        resp += f"🛰️ {server}: ₹ {bal:.2f}\n"
    return resp

def loadTemplate(filename):
    with open(path.join(templates_dir,filename), 'r', encoding='utf-8') as file:
        return file.read()

class BalanceHandler:
    """Handles the balance of users, and also helps in recharge"""
    def __init__(self,image_file='qr.png') -> None:
        if path.isfile(image_file):
            self.img = image_file
        else:
            raise Warning("QR Code for payment is not present")
            
    def openPortal(self, user_id):
        #Here will go the qr code and upi id
        if path.isfile(self.img):
            resp = "Please enter the utr after payment"
            return bot.send_photo(self.img, resp, user_id)
        else:
            raise Warning("QR Code for payment is not present")
        

    def checkUTR(self, message_id, user_id, utr: int):
        response = reply_for_utr(utr,user_id)
        payload = {
            'chat_id': user_id,
            'text': response,
            "reply_to_message_id": message_id
        }
        bot.send_request('sendMessage', payload)

class ShowServices:
    def __init__(self,templates_dir=templates_dir) -> None:
        self.templates_dir = templates_dir
        self.total_pages = 15
        self.pages = {
            'p' + str(i): self._load_page(f'page{str(i)}.txt')
            for i in range(1, self.total_pages + 1)
        }
        self.buttons = self.get_button_rows()
        self.inline_keyboard = [[{
            'text': button_text,
            'callback_data': callback_data
        } for button_text, callback_data in row] for row in self.buttons]

    def _load_page(self, filename):
        return loadTemplate(filename)


    def get_button_rows(self, max_buttons_per_row=5):
        """
      Creates a list of button rows with a maximum of 'max_buttons_per_row' buttons each.

      Args:
          max_buttons_per_row: The maximum number of buttons per row (default 5).

      Returns:
          A list of lists, where each inner list represents a row of buttons with labels.
      """
        buttons = []
        for i in range(1, self.total_pages + 1, max_buttons_per_row):
            # Slice pages for current row
            row_pages = [
                f'p{j}' for j in range(
                    i, min(i + max_buttons_per_row, self.total_pages + 1))
            ]
            # Create button tuples with same labels
            buttons.append(tuple((page, page) for page in row_pages))
        return buttons

    def send_page(self, chat_id, page_key):
        text = self.pages.get(page_key, self.pages['p1'])
        payload = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup':
            json.dumps({'inline_keyboard': self.inline_keyboard})
        }
        return bot.send_request('sendMessage', payload)

    def update_page(self, query, page_key):
        text = self.pages.get(page_key, self.pages['p1'])
        # Update button text based on current page_key (logic here)
        updated_buttons = []
        for row in self.buttons:
            updated_row = []
            for button_text, callback_data in row:
                # modify button text based on logic (e.g., add indicator for current page)
                if button_text == page_key:
                    new_text = f"{button_text}*"  # Example update for current page
                else:
                    new_text = button_text
                updated_row.append({
                    'text': new_text,
                    'callback_data': callback_data
                })
            updated_buttons.append(updated_row)

        # Generate inline keyboard with updated buttons
        updated_inline_keyboard = [[{
            'text': button['text'],
            'callback_data': button['callback_data']
        } for button in row] for row in updated_buttons]

        data = {
            'chat_id':
            query.chat_id,
            'callback_query_id':
            query.callback_query_id,
            'text':
            text,
            'show_alert':
            None,
            'message_id':
            query.message_id,
            'reply_markup':
            json.dumps({'inline_keyboard': updated_inline_keyboard})
        }
        return bot.send_request('editMessageText', data)



main_inline_buttons = [[("Buy Number", "wantNumbers"),
                        ("Buy Fav", "wantFavServices")],
                       [("Recharge ", "recharge"),
                        ("Your Balance", "checkBalance")],
                       [("Order History", "checkHistory")],
                       [("Support", "showSupport")]]

def send_buttons_mini(chat_id,msg_id="", text="Welcome to the Bot",buttons= main_inline_buttons):
    inline_keyboard = [[{
        'text': button_text,
        'callback_data': callback_data
    } for button_text, callback_data in row] for row in buttons]
    payload = {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': json.dumps({'inline_keyboard': inline_keyboard})
    }
    if msg_id != '':
        payload['reply_to_message_id'] = msg_id
    logger.info("Sending message to %s with text: %s", chat_id,
                text[:5])
    bot.send_request('sendMessage', payload)


def send_buttons(update: Message, text="Welcome to the Bot",buttons=None):
    if not buttons:
        buttons = main_inline_buttons
        if isAdmin(update.chat_id):
            buttons =main_inline_buttons + [[("Bot Report", "adminReport"),("Bot Settings","adminSetting")]]
    inline_keyboard = [[{
        'text': button_text,
        'callback_data': callback_data
    } for button_text, callback_data in row] for row in buttons]
    payload = {
        'chat_id': update.chat_id,
        'text': text,
        'reply_to_message_id': update.message_id,
        'reply_markup': json.dumps({'inline_keyboard': inline_keyboard})
    }
    logger.info("Sending message to %s with text: %s", update.chat_id,
                text[:5])
    bot.send_request('sendMessage', payload)

def default_query_update(response:str,query:CallbackQuery):
    inline_keyboard = [[{
        'text': button_text,
        'callback_data': callback_data
    } for button_text, callback_data in row]
                       for row in main_inline_buttons]

    data = {
        'chat_id': query.chat_id,
        'callback_query_id': query.callback_query_id,
        'text': response,
        'show_alert': None,
        "message_id": query.message_id,
        'reply_markup': json.dumps({'inline_keyboard': inline_keyboard})
    }
    return bot.send_request('editMessageText', data)


def forceReply(chat_id,message): 
    payload = {
        "chat_id": chat_id,
        "text": message,
        "reply_markup": {
            "force_reply": True
        }
    }
    return bot.send_request('sendMessage',payload)

services = ShowServices()


def switch_files(file1_path, file2_path):
    """
    Switches two files, deleting the first one and renaming the second to its name.

    Args:
        file1_path: The path to the first file to be deleted.
        file2_path: The path to the second file to be renamed.
    """

    try:
        # Check if both files exist
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            raise FileNotFoundError("One or both files do not exist.")

        # Delete the first file
        os.remove(file1_path)

        # Rename the second file to the first file's name
        os.rename(file2_path, file1_path)

        print(f"Files switched successfully: {file1_path} and {file2_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")