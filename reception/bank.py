import datetime
from requests import get
from .main import reception_api
from secrets_handler import VARIABLES


# Todo : Add Admin feature to change the QR Code and the credentials
def check_amount_received(utr_no
                ,merchantid=VARIABLES['BHARATPE_MERCHANT_ID']
                ,pay_token=VARIABLES['BHARATPE_TOKEN']):
    """To check and validate for any recharge, returns False if no amount received"""

    current_datetime = datetime.datetime.now()
    previous_datetime = current_datetime - datetime.timedelta(hours=72)
    end_date = current_datetime.timestamp()
    start_date = previous_datetime.timestamp()
    url = f"https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions?module=PAYMENT_QR&merchantId={merchantid}&sDate={start_date}&eDate={end_date}"
    headers = {"Token": pay_token}
    response = get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        transactions = data['data']['transactions']
        for transaction in transactions:
            utr = transaction['bankReferenceNo']
            if int(utr) == int(utr_no) and transaction[
                    'status'] == 'SUCCESS':
                var = transaction['amount']
                return var
    
    return False

def reply_for_utr(utr,user_id):
    amount = check_amount_received(utr)
    if not amount:
        return "UTR didnot match, please check it again, or enter after few minutes"
    if reception_api.record_recharge(user_id=user_id,utr=str(utr),amount=amount):
        return "Recharge sucessfull"
    else:
        return "UTR already used, sorry can't repeat"

if __name__=='__main__':
    print(reply_for_utr(428060240254,890642031))
