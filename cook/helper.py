from abc import abstractmethod, ABC

from .models import (offers, phone_detail, serviceInfo, SERVERS, priceResponse, countryInfo)
from .tools import (commonTools, BASE_URL, TOKENS,)
from telegram.bot import logger

tools = commonTools()


class server(ABC):
    @abstractmethod
    def get_phone_number(self, service_code: str, provider: str = 'Any') -> phone_detail:
        """Fetches phone number for the service code and optional provider.

        Args:
            service_code (str): The unique identifier for the service to be fetched.
            provider (str, optional): The service provider from which to fetch the service.
                If not specified, the default provider will be used.

        Returns:
            phone (phone_detail) : Details of phone including its access_id
        """
        pass

    @abstractmethod
    def get_prices(self, service_code) -> list[offers]:
        """Fetches the list of prices for the specified service code along with their corresponding providers.

        Args:
            service_code (str): The unique identifier for the service.

        Returns:
            offer (offers) : A list of tuples, where each tuple contains the provider name and
            the corresponding price for the service.
        """
        pass

    @abstractmethod
    def get_balance(self) -> float:
        """Fetches the current balance in the server"""
        pass

    @abstractmethod
    def check_otp(self, access_id: str) -> str:
        """Checks the OTP status for the given access ID.

        Args:
            access_id (str): The access ID of the service.

        Returns:
            Union[str, None]:
                - The OTP if it has been received.
                - 'canceled' if the service has been canceled.
                - 'waiting' if the OTP is still pending.
                - None if an error occurred or the OTP is not available.
        """
        pass

    @abstractmethod
    def cancel(self, access_id):
        """Tries to cancel the service,
        Returns:
            - True if succesfully canceled,
            - False otherwise
        """
        pass


class FastSMS(server):
    def __init__(self, countryID: int = 22) -> None:
        self.url = BASE_URL['fast']
        self.main_params = {"api_key": TOKENS["fast"], "country": countryID}

    def get_phone_number(self, service_code, provider='Any'):
        params = self.main_params
        params['service'] = service_code
        params['action'] = "getNumber"
        params['country'] = 22
        response = tools.getText(self.url, params=params)
        if not tools.isError(response) and ":" in response:
            _, access, phone = response.split(":")
            return phone_detail(phone=phone, access_id=access)
        else:
            pass

    def get_prices(self, service_code):
        params = self.main_params
        params['action'] = "getPrices"
        params['service'] = service_code
        params['country'] = 22
        response = tools.getJson(BASE_URL['fast'], params=params)
        try:
            price = list(response['22'][service_code].keys())[0]
            count = list(response['22'][service_code].values())[0]
            return [offers('Fast', count=count, cost=price)]
        except:
            pass

    def check_otp(self, access_id: str) -> str:
        params = self.main_params
        params['id'] = access_id
        params['action'] = "getStatus"
        response = tools.getText(self.url, params=params)
        if not tools.isError(response):
            if "WAIT" in response:
                return 'waiting'
            elif "CANCEL" in response:
                return 'cancelled'
            elif "OK" in response:
                return response.split(":")[-1]

    def cancel(self, access_id):
        params = self.main_params
        params['id'] = access_id
        params['status'] = 8
        params['action'] = 'setStatus'
        response = tools.getText(self.url, params=params)
        return response == 'ACCESS_CANCEL'

    def get_balance(self) -> float:
        self.main_params['action'] = "getBalance"
        resp = tools.getText(self.url, params=self.main_params)
        try:
            bal = float(resp.split(":")[-1])
            return bal
        except:
            pass


class tigersms(server):
    def __init__(self) -> None:
        self.url = "https://api.tiger-sms.com/stubs/handler_api.php"
        self.params = {"api_key": TOKENS['tiger']}

    def get_balance(self) -> float:
        params = self.params
        params['action'] = 'getBalance'
        resp = tools.getText(self.url, params=params)
        try:
            bal = float(resp.split(":")[-1])
            return bal
        except ValueError as v:
            pass

    def get_prices(self, service_code):
        base_url = "https://api.tiger-sms.com/stubs/handler_api.php"
        serviceid = service_code
        countrycode = '22'
        params = self.params
        params['action'] = "getPrices"
        params['service'] = serviceid
        params['country'] = countrycode
        response = tools.getJson(base_url, params=params)
        try:
            data = response[countrycode][serviceid]
            return [offers('Tiger', cost=data['cost'], count=data['count'])]
        except:
            pass

    def get_phone_number(self, service_code: str, provider: str = 'Any'):
        params = self.params
        params['service'] = service_code
        params['action'] = "getNumber"
        params['country'] = '22'
        params['ref'] = 'Nothing'
        response = tools.getText(self.url, params)
        if not tools.isError(response) and ":" in response:
            _, access, phone = response.split(":")
            return phone_detail(phone, access)
        else:
            pass

    def check_otp(self, access_id: str) -> str:
        """
          Possible Answers
          ANSWER:
          STATUS_WAIT_CODE - Waiting for SMS
          STATUS_WAIT_RESEND - waiting for next SMS
          STATUS_CANCEL - activation canceled
          STATUS_OK: 'activation code' - code received
          POSSIBLE MISTAKES:
          BAD_KEY - invalid API key
          BAD_ACTION - incorrect action
          NO_ACTIVATION - incorrect activation id
        """
        params = self.params
        params['id'] = access_id
        params['action'] = "getStatus"
        response = tools.getText(self.url, params=params)
        if not tools.isError(response):
            if "WAIT" in response:
                return 'waiting'
            elif "CANCEL" in response:
                return 'cancelled'
            elif "OK" in response:
                return response.split(":")[-1]

    def cancel(self, access_id):
        """
        Change the status of the given access ID,
        1 - inform about the readiness of the number (SMS sent to the number)
        3 - request another code (free)
        6 - complete activation *
        8 - inform that the number has been used and cancel the activation
        """
        """
        ** if there was a status 'code received' - marks it successfully and completes, if there was a 'preparation' - 
        deletes and marks an error, if there was a status 'ing retry' - transfers activation to SMS pending

        ** It is not possible to change the activation status for which the verification method by call was selected 
        if the number has already arrived

        ANSWER:
        ACCESS_READY - phone is ready for getting SMS
        ACCESS_RETRY_GET - waiting for a new SMS
        ACCESS_ACTIVATION - the service has been successfully activated
        ACCESS_CANCEL - activation canceled

        POSSIBLE MISTAKES:
        NO_ACTIVATION - incorrect activation id
        BAD_SERVICE - incorrect service name
        BAD_STATUS - incorrect status
        BAD_KEY - invalid API key
        BAD_ACTION - incorrect action
        """

        params = self.params
        params['id'] = access_id
        params['status'] = str(8)
        params['action'] = 'setStatus'

        response = tools.getText(self.url, params=params)
        if not tools.isError(response):
            return "CANCEL" in response


class bowersms(server):
    def __init__(self):
        self.url = "https://smsbower.com/stubs/handler_api.php"
        self.params = {"api_key": TOKENS['bower']}

    def get_balance(self) -> float:
        params = self.params
        params["action"] = "getBalance"
        resp = tools.getText(self.url, params=params)
        try:
            bal = float(resp.split(":")[-1])
            return bal
        except:
            pass

    def get_prices(self, service_code):
        params = self.params
        serviceCode = service_code
        countryCode = '22'
        params['action'] = "getPrices"
        params['service'] = serviceCode
        params['country'] = countryCode
        response = tools.getJson(self.url, params=params)
        if tools.isError(response):
            return None
        try:
            data = response[countryCode][serviceCode]  # cost and count
            return [offers('Bower', count=data['count'], cost=data['cost'])]
        except:
            pass

    def get_phone_number(self, service_code: str, provider: str = 'Any'):
        params = self.params
        params['service'] = service_code
        params['action'] = "getNumber"
        params['country'] = '22'
        params['maxPrice'] = '100'  # Max Price for the phone number
        # To get a new number needs old number
        # params['phoneException'] = 987654321
        # params['ref'] = 'none'
        response = tools.getText(self.url, params=params)
        if not tools.isError(response) and ":" in response:
            _, access, phone = response.split(":")
            return phone_detail(phone=phone, access_id=access)

    def check_otp(self, access_id: str) -> str:
        """
          Answer
          STATUS_WAIT_CODE - Waiting for SMS
          STATUS_WAIT_RESEND - Waiting for next sms
          STATUS_CANCEL - Activation canceled
          STATUS_OK: 'activation code' - code received
          Possible mistakes
          BAD_KEY - invalid API key
          BAD_ACTION - incorrect action
          NO_ACTIVATION - incorrect activation id
        """
        params = self.params
        params['id'] = access_id
        params['action'] = "getStatus"
        response = tools.getText(self.url, params=params)

        if not tools.isError(response):
            if "WAIT" in response:
                return 'waiting'
            elif "CANCEL" in response:
                return 'cancelled'
            elif "OK" in response:
                return response.split(":")[-1]

    def cancel(self, access_id):
        """Change the status of the given access ID,
          activation status code 
          1 - inform about the readiness of the number (SMS sent to the number)
          3 - request another code (free)
          6 - complete activation *
          8 - inform that the number has been used and cancel the activation

          Returns 
          ANSWER
          ACCESS_READY - phone is ready for getting SMS
          ACCESS_RETRY_GET - waiting for a new SMS
          ACCESS_ACTIVATION - the service has been successfully activated
          ACCESS_CANCEL - activation canceled
          Possible mistakes
          NO_ACTIVATION - incorrect activation id
          BAD_SERVICE - incorrect service name
          BAD_STATUS - incorrect status
          BAD_KEY - invalid API key
          BAD_ACTION - incorrect action
          EARLY_CANCEL_DENIED - It is possible to cancel the number after 2 minutes following the purchase

          """

        params = self.params
        params['id'] = access_id
        params['status'] = str(8)
        params['action'] = "setSatus"

        response = tools.getText(self.url, params=params)
        if not tools.isError(response):
            return "CANCEL" in response


class fivesimsms(server):
    def __init__(self):
        self.token = TOKENS["5Sim"]
        self.headers = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/json',
        }

        self.country = 'india'

    def get_balance(self) -> float:
        url = 'https://5sim.net/v1/user/profile'
        response = tools.getJson(url,
                                 headers=self.headers)
        try:
            bal = float(response['balance'])
            return bal
        except:
            pass

    def get_prices(self, service_code):

        countryCode = 'india'
        if not service_code:
            return None
        params = {
            'product': service_code,
            'country': countryCode
        }

        response = tools.getJson('https://5sim.net/v1/guest/prices',
                                 headers=self.headers,
                                 params=params)
        try:
            respond = response[countryCode][service_code]
            lis = []
            for key, val in respond.items():
                if val['count'] == 0:
                    continue
                lis.append(offers('5Sim', key, val['count'], val['cost']))
            return lis
        except Exception:
            pass

    def get_phone_number(self, service_code: str, provider: str = 'Any') -> phone_detail:
        country = self.country
        product = service_code
        operator = provider
        url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
        response = tools.getJson(url,
                                 headers=self.headers)
        try:
            phone = response['phone']
            id = str(response['id'])
            return phone_detail(phone, id)
        except:
            pass

    def check_otp(self, access_id: str) -> str:
        """"
        PENDING - Preparation
        RECEIVED - Waiting of receipt of SMS
        CANCELED - Is cancelled
        TIMEOUT - A timeout
        FINISHED - Is complete
        BANNED - Number banned, when number already used
        """

        url = 'https://5sim.net/v1/user/check/' + access_id
        response = tools.getJson(url,
                                 headers=self.headers)
        if tools.isError(response):
            return 'Invalid'
        else:
            try:
                # Returning the last OTP Received
                if "PENDING" in response['status']:
                    return 'waiting'
                elif response['status'] in ['CANCELED', 'TIMEOUT', 'BANNED']:
                    return 'canceled'
                elif response['status'] in ['RECEIVED', 'FINISHED']:
                    if response['sms']:
                        return response['sms'][-1]['code']
                    else:
                        return 'waiting'
            except:
                pass

    def cancel(self, access_id):
        url = f'https://5sim.net/v1/user/cancel/' + str(access_id)
        response = tools.getJson(url,
                                 headers=self.headers)
        if tools.isError(response):
            return False
        try:
            return response['status'] == "CANCELED/FINISHED"
        except ValueError:
            return False


class api_requests():
    def __init__(self):
        self.fast = FastSMS()
        self.tiger = tigersms()
        self.bower = bowersms()
        self.five = fivesimsms()
        self.server = {
            "Fast": self.fast,
            "Tiger": self.tiger,
            "Bower": self.bower,
            "5Sim": self.five
        }

    def get_balance(self, serverName: SERVERS):
        server = self.server[serverName]
        bal = server.get_balance()
        if not isinstance(bal,float):
            bal = -9.99
            logger.error(f"Failed to fetch server balance at {serverName}")
        return {serverName: bal}

    def getPricesFromName(self, serviceName: str):
        service_info = tools.getServiceInfo(serviceName, country=countryInfo())
        if service_info is None:
            return "Service not found"

        lis = []
        error_price = lambda server: logger.error(f"Error in getting price from {server} for {service_info.name}")
        if service_info.bowerCode:
            try:
                lis += self.bower.get_prices(service_info.bowerCode)
            except:
                error_price('Bower')
        if service_info.tigerCode:
            try:
                lis += self.tiger.get_prices(service_info.tigerCode)
            except:
                error_price('Tiger')
        if service_info.fastCode:
            try:
                lis += self.fast.get_prices(service_info.fastCode)
            except:
                error_price('Fast')
        if service_info.fiveCode:
            try:
                lis += self.five.get_prices(service_info.fiveCode)
            except:
                error_price('5Sim')
        return priceResponse(service=service_info, offers=lis)

    def getPhoneFromName(self, server_name: SERVERS,
                         serviceName: str = None,
                         provider: str = 'Any') -> phone_detail:
        serviceinfo = tools.getServiceInfo(serviceName, countryInfo())
        return self.server[server_name].get_phone_number(self.get_service_code(server_name, serviceinfo), provider)

    def get_otp(self, server_name: SERVERS,
                access_id: str,
                ) -> str:
        server = self.server[server_name]
        return server.check_otp(access_id)

    def get_service_code(self, server_name: SERVERS, service_info: serviceInfo):
        if server_name == '5Sim': return service_info.fiveCode
        if server_name == 'Bower': return service_info.bowerCode
        if server_name == 'Fast': return service_info.fastCode
        if server_name == 'Tiger': return service_info.tigerCode

    def cancelPhone(self, serverName: SERVERS, access_id: str):
        server = self.server[serverName]
        return server.cancel(access_id)  # server.cancelService(access_id)


def manualtest():
    fs = bowersms()
    service = 'amf'
    prices = fs.get_prices(service)
    if not prices:
        return
    print(prices)
    x = input()
    ph = fs.get_phone_number(service, x)
    print(ph)
    cancel = fs.cancel(ph.access_id)
    print(cancel)


def manualtest2():
    api = api_requests()
    balances = []
    for i in ['Fast', 'Tiger', '5Sim', 'Bower']:
        balances.append(api.get_balance(i))
    print(balances)

    service = input('Service Name :')
    prices = api.getPricesFromName(service)
    print(prices)

    server = input('Server Name :')
    provider = input('Provider :')
    phone = api.getPhoneFromName(server, service, provider)
    print(phone)

    while True:
        query = input('Cancel/Check OTP')
        if query.lower() == 'cancel':
            print(api.cancelPhone(server, phone.access_id))
            break
        else:
            update = api.get_otp(server, phone.access_id)
            print(f"Status for {phone} is :{update}")


if __name__ == '__main__':
    manualtest2()
