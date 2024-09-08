import datetime
from os import getenv
from dotenv import load_dotenv
from requests import get
from .main import UserDatabase

load_dotenv()

def check_amount_received(utr_no):
    """To check and validate for any recharge, returns False if no amount received"""
    current_datetime = datetime.datetime.now()
    previous_datetime = current_datetime - datetime.timedelta(hours=72)
    end_date = current_datetime.timestamp()
    start_date = previous_datetime.timestamp()

    url = f"https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions?module=PAYMENT_QR&merchantId=34672612&sDate={start_date}&eDate={end_date}"
    headers = {"Token": getenv("BHARATPE_TOKEN")}

    response = get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        transactions = data['data']['transactions']
        for transaction in transactions:
            # print(utr_no)
            if transaction['bankReferenceNo'] == utr_no and transaction[
                    'status'] == 'SUCCESS':
                var = transaction['amount']
                return var
    
    return False

def reply_for_utr(utr,user_id):
    amount = check_amount_received(utr)
    if not amount:
        return "UTR didnot match, please check it again, or enter after few minutes"
    if UserDatabase().record_recharge(user_id=user_id,utr=utr,amount=amount):

        return "Recharge sucessfull"
    else:
        return "UTR already used, sorry can't repeat"


