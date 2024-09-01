from .helper_phone import otpUpdateQuery,requestNumber
from telegram.models import CallbackQuery
from .helper import default_query_update, services, BalanceHandler,loadTemplate
from .cook import serviceOps
from telegram.bot import bot, logger
from reception.main import reception_api


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
    if q == "wantNumbers":
        return services.send_page(query.chat_id, 'p1')
    elif q in services.pages:
        return services.update_page(query, q)
    elif q == "checkBalance":
        bal = reception_api.see_balance(user_id=user_id)
        response = f"Your Balance is {bal} "
    elif q == "recharge":
        return BalanceHandler().openPortal(user_id)
    elif q == "checkHistory":
        response = " Check History here\n"
        txn = reception_api.see_transactions(user_id)
        response+=txn
    #Checking for OTP and Canceling Queries
    elif 'buy' == q[:3]:
        _,server,service_name,provider = q.split('_')
        logger.log(3,f"{user_name} buy {service_name,server,provider}")
        return requestNumber(server,service_name,provider,user_id,user_name)
        
    elif "chk" in q:
        #{s_name}_{price}
        n, act_code, phoneNo, sname, price,server = q.split("_")
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
                             server=server)
    elif "cancel" in q:
        # Once check for OTP the last time, before canceling
        _, act_code, sname, price,server = q.split("_")
        x = serviceOps.cancelPhone(server,act_code)
        if x:
            response = f"The {sname} is deactivated, and money refunded"
            reception_api.add_transactions(user_id, f"{sname} CANCELED", -float(price))
            logger.log(5, f"{user_id} cancelled {sname}")
        else:
            logger.error(
                f"{sname} couldnot deactivate, no refund yet {user_id}")
            response = "There was issue with deactivation and refund\nPlease get back to support team"
            return bot.send_message(user_id,response)
    elif "againOTP" in q:
        return bot.send_message(user_id,"Requesting more otp is not allowed now.")
        

    elif "showSupport" in q:
        response = loadTemplate("support.txt")
    else:
        response = "You clicked for " + query.data
        #These will change the message text for the queries

    data = {
        'callback_query_id': query.callback_query_id,
        'text':response
    }
    bot.send_request('answerCallbackQuery',data)
    default_query_update(response, query=query)

