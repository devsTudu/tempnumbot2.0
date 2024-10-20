from .helper import send_buttons,services,BalanceHandler, loadTemplate,isAdmin,forceReply
from .helper_phone import showAvailableServer
from telegram.bot import bot,logger
import waiter.cook_helper as ch
from telegram.models import Message
from reception.main import reception_api
from secrets_handler import VARIABLES
from .admin_setup import handle_admin

#Command Handler
class Commands:
    def __init__(self,update:Message) -> None:
        self.update = update
        self.name = update.user_first_name
        self.user_id = update.user_id
        self.commands_map ={
            "/start":self.start,
            "/getnum":self.getnum,
            "/checkbal":self.checkbal,
            "/recharge":self.recharge,
            "/seefav":self.getfavlist,
            "/seehist":self.checkhistory,
            "/referal":self.getreferral,
            "/update_prices":self.update_price,
            "/update_payment":self.update_payment
        }
        
    def run(self):
        command = self.update.text
        if "ser_" in command:
            service_code = str(command)[5:]
            # This will check for the available services for this number
            return showAvailableServer(service_code,self.update)
        try:
            return self.commands_map[command]()
        except KeyError as e:
            logger.error(str(e))
            bot.reply_message(self.user_id,self.update.message_id,
                            "Invalid Command")
            
        
    def start(self):
        welcome_msg = loadTemplate("welcome_message.txt")
        response = f"Hi, {self.name}, welcome to the \n"
        response += welcome_msg
        return send_buttons(self.update,response)

    def getnum(self):
        return services.send_page(self.user_id, 1)

    def checkbal(self):
        bal = reception_api.see_balance(self.user_id)
        response = f"Your Balance is {bal:.2f} "
        return send_buttons(self.update,response)

    def recharge(self):
        return BalanceHandler().openPortal(self.user_id)

    def checkhistory(self):
        response = " Check History here\n"
        txn = ''+reception_api.see_transactions(user_id=self.user_id)
        return send_buttons(self.update,response+txn)
    
    def getfavlist(self):
        lis = reception_api.get_favourite_services(user_id=self.user_id)
        resp = ch.serviceOps.list_items_with_commands(lis)
        return send_buttons(self.update,
                            "Your Favourite List appears here\n"
                            +resp)

    def update_price(self):
        if isAdmin(self.user_id) :    
            resp = f"Please enter the new profit rate, Current is {VARIABLES['PROFIT_RATE']}"
            return forceReply(self.user_id,resp)
        else:
            return bot.reply_message(self.update.chat_id,
            self.update.message_id,"Invalid Command")

    def update_payment(self):
        if isAdmin(self.user_id):    
            resp = f"Please send me the new QR Code with <BHARATPE_MERCHANT_ID>:<BHARATPE_TOKEN> as caption"
            return forceReply(self.user_id,resp)
        else:
            return bot.reply_message(self.user_id,
            self.update.message_id,"Invalid Command")


    def getreferral(self):
        return send_buttons(self.update,"Your referral scores")
        

#Handle the messages
def respond_to(request):
    try:
        update = Message(request)
        logger.info("%s messaged: %s",
                    update.user_first_name, update.text)
    except Exception as e:
        logger.critical("Invalid Message request")
        raise e
    try:
        # Addition for the admin feature
        user_id = request['message']['from']['id']
        if isAdmin(user_id):
            return handle_admin(request)
        
    except Exception as e:
        pass
        
    if update.is_command:
        commands = Commands(update=update)
        commands.run()
    elif update.text.isdigit():
        return BalanceHandler().checkUTR(update.message_id, update.user_id,
                                  int(update.text))
    elif "/" not in update.text:
        return sendSearchResult(update)
    else:
        return bot.reply_message(update.chat_id, update.message_id,
                          "We are working on it")


#Handle Search Query
def sendSearchResult(update: Message):
    result = ch.serviceOps.fuzzy_search(update.text, 50)
    if "Not" in result:
        response = "Sorry the search term didn't match with any service we offer"
    else:
        response = "Are you looking for them.."
        for index, element in enumerate(result):
            response += f"\n{index+1} {element[1]} /ser_{element[2]}"
    return bot.send_message(update.chat_id, response)     

