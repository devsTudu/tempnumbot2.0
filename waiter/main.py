from telegram.bot import bot,logger
from .query_handler import answer_to
from .message_handler import respond_to

def workOn(request):
    if 'callback_query' in request:
        return answer_to(request)
    elif 'message' in request:
        return respond_to(request)
    else:
        print(request)
        logger.warning("Unusual Request")

#Set the Webhook
def setWebhook(url):
    url =  (url.split(sep="/"))[2]
    data = {
        "url":url+'/bot'
    }
    return bot.send_request("setWebhook",data)

def setmanualhook(url):
    data = {
        "url":url
    }
    return bot.send_request("setWebhook",data)