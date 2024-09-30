from logging import log
from .models import SERVERS, phone_detail, phoneDetails
from .helper import api_requests
import asyncio

req = api_requests()
async def get_price_from_name(servicename:str):
    try:
        resp = await req.getPricesFromName(serviceName=servicename)
    except Exception as e:
        log(2,f"Error getting price for {servicename}")
        resp = "Error fetching prices you can try again"
    return resp

async def get_phone_number(server,
                     service_name: str = None,
                     provider: str = 'Any',
                     user: str = "123456789"):
    try:
        resp = await req.getPhoneFromName(server,service_name,provider)
    except Exception as e:
        log(2,f"Error getting phone number for {service_name,provider,server} by {user}")
        resp = "Error getting number for you try again"
    return resp

async def get_updates(server: SERVERS,
                access_id: str,
                *kwargs):
    """Get the otp update for a given phone number details"""

    resp = await req.get_otp(server_name=server,
                                          access_id=access_id)

    if not isinstance(resp, str):
        log(2,f'Error getting update for the {server,access_id}')
        resp = 'Error getting update'
    return resp


async def cancel_phone(server: SERVERS, access_id: str):
    """Cancel the otp update for a given phone number details,

    Returns True if Sucessfully Canceled Phone Number"""

    return await req.cancelPhone(serverName=server,
                                            access_id=access_id)
    


async def test_services():
    name = 'Telegram'
    server = 'Tiger'
    prices = await get_price_from_name(name)
    print(prices)
    phone = await get_phone_number(server,name)
    print(phone)
    if not isinstance(phone,phone_detail):
        return 'Failed getting phone number'
    while True:
        query = input('Cancel/Check OTP')
        if query.lower() == 'cancel':
            print( await cancel_phone(server,phone.access_id))
            break
        else:
            update = await get_updates(server,phone.access_id)
            print(f"Status for {phone} is :{update}")




if __name__=='__main__':
    asyncio.run(test_services())
