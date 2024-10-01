from reception.main import reception_api
from telegram.models import Message
from .cook import serviceOps
from .helper import send_buttons, BalanceHandler
from telegram.bot import bot, logger
import json


#Get Phone Number Sequence
async def showAvailableServer(service_code, update: Message,service_name=''):
    if service_name == '':
        service_name = serviceOps.getServiceName(service_code)
    buttons = await serviceOps.getServerListButtonFor(service_name)
    if buttons is None or len(buttons) == 0:
        return bot.reply_message(
            update.chat_id, update.message_id,
            f"Sorry, No server available for {service_name} Now.")

    msg = f"The {service_name} has these options"
    return send_buttons(update, msg, buttons)


def sendMessageforNumber(chat_id, user_firstName, s_phone, s_name, s_price:float,
                         s_actCode,server,provider):
    
    reception_api.add_orders(chat_id,s_name,-abs(s_price))
    response = f"here is your {str(s_phone)[:-10]} `{str(s_phone)[-10:]}` for {s_name}\n"
    logger.log(
        2, f"Phone for {user_firstName}({chat_id}) generated for {s_name}")
    inline_button = [[{
        "text":"Check for OTP",
        "callback_data":
        f"chk_{s_actCode}_{s_phone}_{s_name}_{s_price}_{server}_{provider}"
    }]]
    payload = {
        'chat_id': chat_id,
        'text': response,
        'reply_markup': json.dumps({'inline_keyboard': inline_button}),
        "parse_mode": "Markdown"
    }
    print(payload)
    return bot.send_request('sendMessage',payload)

# Come and use this function
def requestNumber(server,service_name,provider, chat_id, user_firstName):
    s_price = serviceOps.fetchPrice(server=server,
                                   service_name=service_name,
                                   provider=provider)
    if s_price>=999:
        # The price when it fails to get the actual price
        logger.error("Failed getting number for " + service_name)
        bot.send_message(chat_id, "Sorry there was an issue getting your number for " +service_name +",\nDevelopers are notified about this and will come back to you")
        return         
    user_balance = reception_api.see_balance(user_id=chat_id)
    if float(user_balance) < float(s_price):
        resp = f"Sorry, {user_firstName} your balance is {user_balance}, and the price for this service is {s_price}"
        bot.send_message(chat_id, resp)
        return BalanceHandler().openPortal(user_id=chat_id)
    try:
        #Generate Phone Number
        data = serviceOps.getPhoneNumber(service_name,
                                                       server,
                                                       provider)
        #Record the Transaction
        return sendMessageforNumber(chat_id, user_firstName,
                                    data['phone'],
                                    service_name,
                                    float(s_price),
                                    data['access_id'],server=data['server'],provider=provider)
    except ValueError:
        logger.error("Failed getting number for " + service_name)
        bot.send_message(chat_id, "Sorry there was an issue getting your number for " +service_name +",\nDevelopers are notified about this and will come back to you")
    except TypeError as t:
        logger.error(t)
        bot.send_message(chat_id, "Sorry there was an issue getting your number for " +service_name +",\nDevelopers are notified about this and will come back to you")
        
        

#Handle the requests for updates on OTP after getting
def otpUpdateQuery(phoneNo, act_code, user_id, message_id, s_name, price, n,server,provider):
    response = f"Your number : {str(phoneNo)[:-10]} `{str(phoneNo)[-10:]}`"
    response += f"\n for {s_name}"
    otp = serviceOps.getOTP(server,act_code)
    if otp == -1:
        # OTP is cancelled or Expired
        response += "\n is Canceled or Expired"
        #user_db.record_order(user_id, f"{s_name} CANCELED", -int(price))
        reception_api.add_orders(user_id,f"{s_name} CANCELED", -int(price))
        response += "\n And money refunded."
        inline_button = [[{
            "text":"Buy Again",
            "callback_data":f"buyagain_{s_name}_{price}_{server}_{provider}"
}]]
        payload = {
            'chat_id': user_id,
            'text': response,
            'message_id': message_id,
            "parse_mode": "Markdown",
            'reply_markup': json.dumps({'inline_keyboard': inline_button})
        }
        return bot.send_request("editMessageText", payload)
    elif otp == 0:
        response += f"\n Is waiting for OTP ({n})"
        #Only to return when the OTP is waiting
        inline_button = [[{
            "text":
            "Check for OTP",
            "callback_data":
            f"chk{n+1}_{act_code}_{phoneNo}_{s_name}_{price}_{server}_{provider}"
        }]]
        if n % 5 == 4:
            inline_button.append([{
                "text":
                "Cancel this",
                "callback_data":
                f"cancel_{act_code}_{s_name}_{price}_{server}"
            }])
        payload = {
            'chat_id': user_id,
            'text': response,
            'message_id': message_id,
            'parse_mode': "Markdown",
            'reply_markup': json.dumps({'inline_keyboard': inline_button})
        }
        return bot.send_request('editMessageText', payload)
    else:
        response += f"\n Recieved OTP : `{otp}`"
        #When OTP success
        inline_button = [[{
            "text":
            "Need OTP again",
            "callback_data":
            f"againOTP_{act_code}_{phoneNo}_{s_name}_{price}_{server}"
        }],
                         [{
            "text":
            "Buy Again",
            "callback_data":
            f"buyagain_{s_name}_{price}_{server}_{provider}"
        }]
                         ]
        payload = {
            'chat_id': user_id,
            'text': response,
            'message_id': message_id,
            "parse_mode": "Markdown",
            'reply_markup': json.dumps({'inline_keyboard': inline_button})
        }
        return bot.send_request("editMessageText", payload)
