import io
from logging import log

from .helper import api_requests
from .models import SERVERS, phone_detail

req = api_requests()


def get_price_from_name(servicename: str):
    try:
        resp = req.getPricesFromName(serviceName=servicename)
    except:
        log(2, f"Error getting price for {servicename}")
        resp = "Error fetching prices you can try again"
    return resp


def get_phone_number(server,
                     service_name: str = None,
                     provider: str = 'Any',
                     user: str = "123456789"):
    try:
        resp = req.getPhoneFromName(server, service_name, provider)
    except Exception as e:
        log(2, f"Error getting phone number for {service_name, provider, server} by {user},{e}")
        resp = "Error getting number for you try again"
    return resp


def get_updates(server: SERVERS,
                access_id: str,
                *kwargs):
    """Get the otp update for a given phone number details"""

    resp = req.get_otp(server_name=server,
                       access_id=access_id)

    if not isinstance(resp, str):
        log(2, f'Error getting update for the {server, access_id}')
        resp = 'Error getting update'
    return resp


def cancel_phone(server: SERVERS, access_id: str):
    """Cancel the otp update for a given phone number details,

    Returns True if Sucessfully Canceled Phone Number"""

    return req.cancelPhone(serverName=server,
                           access_id=access_id)


def manual_test():
    name = 'Telegram'
    server_name = 'Tiger'
    prices = get_price_from_name(name)
    print(prices)
    phone = get_phone_number(server_name, name)
    print(phone)

    if not isinstance(phone, phone_detail):
        return 'Failed getting phone number'
    while True:
        query = input('Cancel/Check OTP')
        if query.lower() == 'cancel':
            print(cancel_phone(server_name, phone.access_id))
            break
        else:
            update = get_updates(server_name, phone.access_id)
            print(f"Status for {phone} is :{update}")

def test_services():
    name = 'Probo'
    server = 'Fast'
    prices = get_price_from_name(name)
    price = [serve['cost'] for serve in list(map(vars , prices.offers)) if serve['server']==server][0]
    assert isinstance(price, float)

    phone = get_phone_number(server, name)
    assert isinstance(phone,phone_detail)
    assert cancel_phone(server, phone.access_id) , "Error cancelling phone number"


if __name__ == '__main__':
    manual_test()
