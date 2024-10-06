import waiter.cook_helper as ch
from secrets_handler import VARIABLES
from telegram.bot import bot
from .helper import forceReply,send_buttons_mini
from reception.bank import check_amount_received

import os
import requests


MERCH_ID = VARIABLES['BHARATPE_MERCHANT_ID']
PAYMENT_TOKEN = VARIABLES['BHARATPE_TOKEN']

def handle_admin(request):
    user_id = request['message']['from']['id']
    if request['message']['reply_to_message']:
        text = request['message']['reply_to_message']['text']
        if "Please enter the new profit rate" in text:
            try:
                reply = request['message']['text']
                rate = int(reply)
                VARIABLES['PROFIT_RATE'] = rate
                ch.SALES_PRICE = lambda x: int(float(x) * (1 + rate / 100) + 1)
            except:
                resp = "rate should be an integer from 1-99"
            finally:
                return bot.send_message(user_id, f"The updated rate is {VARIABLES['PROFIT_RATE']}")

        elif "Please send me the new QR Code" in text:
            # Update QR Code
            caption = request['message']['caption']
            merchid,token = caption.split(':')
            VARIABLES['MERCHID'] = merchid
            VARIABLES['TOKEN_NEW'] = token
            file_id = request['message']['photo'][-1]['file_id']
            image_path = download_image(file_id)
            resp = f"MerchID:{merchid} \nToken:{token}"
            bot.send_photo(image_path,resp,user_id)
            resp = "You can do a payment for test."
            return forceReply(user_id, resp)
        elif "payment for test" in text:
            utr = reply = request['message']['text']
            msg_id = request['message']['message_id']
            token = VARIABLES['TOKEN_NEW']
            merchid = VARIABLES['MERCHID']
            val = check_amount_received(utr,merchid,token)
            if val:
                btn = [[('Activate',f'activate_{MERCH_ID}_{PAYMENT_TOKEN}')]]
                resp = f"We could receive {val}, the settings work fine"
                return send_buttons_mini(user_id,msg_id,resp,btn)
            else:
                bot.reply_message(user_id,msg_id,"Sorry the UTR didnot work, the QR not changed")
                return forceReply(user_id,"Try again the UTR")

            






def download_image(file_id):
    """Downloads an image from Telegram using its file ID."""
    bot_token = VARIABLES['BOT_TOKEN']
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(url)
    file_path = response.json()['result']['file_path']
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    image_data = requests.get(download_url).content
    file_path = 'new_qr.jpg'
    with open(file_path, 'wb') as f:
        f.write(image_data)
    return file_path
