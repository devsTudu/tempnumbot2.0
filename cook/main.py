from logging import log
from models import SERVERS, phoneDetails
from helper import api_requests
import asyncio

req = api_requests()
def get_price_from_name(servicename:str):
    try:
        resp = req.getPricesFromName(serviceName=servicename)
    except Exception as e:
        log(2,f"Error getting price for {servicename}")
        resp = "Error fetching prices"
    return resp

def get_phone_number(server,
                     service_name: str = None,
                     provider: str = 'Any',
                     user: str = "123456789"):
    try:
        resp = req.getPhoneFromName(server,service_name,provider,user)
    except Exception as e:
        log(2,f"Error getting phone number for {service_name,provider,server} by {user}")
        resp = "Error getting number for you"
    return resp

def get_updates(server: SERVERS,
                access_id: str,
                phone=987654321):
    """Get the otp update for a given phone number details"""

    resp = req.getStatus(serverName=server,
                                          access_id=access_id,
                                          phone=phone)

    if not isinstance(resp, phoneDetails):
        log(2,f'Error getting update for the {server,access_id}')
        resp = 'Error'
    return resp


def cancel_phone(server: SERVERS, access_id: str):
    """Cancel the otp update for a given phone number details,

    Returns True if Sucessfully Canceled Phone Number"""

    resp = req.cancelPhone(serverName=server,
                                            access_id=access_id)
    return resp


def test_services():
    name = 'Telegram'
    prices = asyncio.run(get_price_from_name(name))
    print(prices)


if __name__=='__main__':
    test_services()
