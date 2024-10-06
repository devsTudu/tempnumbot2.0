from .helper_phone import otpUpdateQuery,requestNumber
from telegram.models import CallbackQuery
from .helper import default_query_update, services, BalanceHandler,loadTemplate,report_balance,report_reception,switch_files
from .cook_helper import serviceOps
from telegram.bot import bot, logger
from reception.main import reception_api
from secrets_handler import VARIABLES


def answer_to(request):
    try:
        query = CallbackQuery(request)
    except Exception as e:
        logger.critical("Invalid Query Received")
        raise e from None
    q = query.data
    user_id = query.chat_id
    user_name = query.from_user_username
    # These handles the pages in the show services
    try:
        if q == "wantNumbers":
            return services.send_page(query.chat_id, 'p1')
        elif q in services.pages:
            return services.update_page(query, q)
        elif q == "checkBalance":
            bal = reception_api.see_balance(user_id=user_id)
            response = f"Your Balance is {bal:.2f} "
        elif q == "recharge":
            return BalanceHandler().openPortal(user_id)
        elif q == "checkHistory":
            response = " Check History here\n"
            txn = reception_api.see_transactions(user_id)
            response+=txn
        #Checking for OTP and Canceling Queries
        
        elif 'buyagain' in q:
            # buyagain_{s_name}_{price}_{server}_{provider}
            _,service_name,price,server,provider = q.split('_')
            logger.log(3,f"{user_name} rebuys {service_name,server,provider}")
            return requestNumber(server,service_name,provider,user_id,user_name)

        elif 'buy' == q[:3]:
            _,server,service_name,provider = q.split('_')
            logger.log(3,f"{user_name} buy {service_name,server,provider}")
            return requestNumber(server,service_name,provider,user_id,user_name)
            
        elif "chk" in q:
            #chk{n+1}_{act_code}_{phoneNo}_{s_name}_{price}_{server}_{provider}
            n, act_code, phoneNo, sname, price,server,provider = q.split("_")
            try:
                n = int(n.split('chk')[-1])
            except ValueError:
                n = 1
            return otpUpdateQuery(phoneNo,
                                act_code,
                                user_id,
                                query.message_id,
                                s_name=sname,
                                price=price,
                                n=n,
                                server=server,
                                provider=provider)
        elif "cancel" in q:
            # Once check for OTP the last time, before canceling
            _, act_code, sname, price,server = q.split("_")
            x = serviceOps.cancelPhone(server,act_code)
            if x:
                response = f"The {sname} is deactivated, and money refunded"
                reception_api.add_orders(user_id, f"{sname} CANCELED", float(price))
                logger.log(5, f"{user_id} cancelled {sname}")
            else:
                logger.error(
                    f"{sname} couldnot deactivate, no refund yet {user_id}")
                response = {
                    "callback_query_id": query.callback_query_id,
                    'text':"There was issue with deactivation"
                    }
                
                return bot.send_request('answerCallbackQuery',response)
                # return bot.send_message(user_id,response)
        elif "againOTP" in q:
            return bot.send_message(user_id,"Requesting more otp is not allowed now.")
        
            
        elif "showSupport" in q:
            response = loadTemplate("support.txt")
        elif "wantFavServices" in q:
            lis = reception_api.get_favourite_services(user_id=user_id)
            response = serviceOps.list_items_with_commands(lis)
        elif "adminReport" in q:
            response = "Server Balances 🌐 \n" + str(report_balance())
            response += "\n Reports \n" + str(report_reception())
        elif "adminSetting" in q:
            response = loadTemplate("admin_option.txt")
        elif "activate" in q:
            _, merch_id, token = q.split('_')
            try:
                VARIABLES['BHARATPE_MERCHANT_ID'] = merch_id
                VARIABLES['BHARATPE_TOKEN'] = token
                switch_files('qr.png','new_qr.jpg')
                response = "New Payment Updated"
            except Exception as e:
                logger.exception(e)
                response = '‼️ New Payment update failed'
        else:
            response = "You clicked for " + query.data
            #These will change the message text for the queries
    except:
        response = "Some error occcured, please try again"
    data = {
        'callback_query_id': query.callback_query_id,
        'text':response
    }
    bot.send_request('answerCallbackQuery',data)
    default_query_update(response, query=query)

