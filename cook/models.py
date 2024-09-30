from typing import Literal

SERVERS = Literal['Fast', 'Tiger', '5Sim', 'Bower']

# Data Model Declaration
class countryInfo:
    def __init__(self, name='india', code='22'):
        self.name = name
        self.code = code
    def __repr__(self) -> str:
        return self.name

class serviceInfo:
    def __init__(self, name, fastCode=None, tigerCode=None, bowerCode=None, fiveCode=None, country=countryInfo):
        self.name = name
        self.fastCode = fastCode
        self.tigerCode = tigerCode
        self.bowerCode = bowerCode
        self.fiveCode = fiveCode
        self.country = country

    def __repr__(self) -> str:
        return f"S.Info(Name:{self.name},country:{self.country})"

class serviceDetails:
    def __init__(self, server, serviceInfo, provider='Any', count=1, cost=1.0):
        self.server = server
        self.serviceInfo = serviceInfo
        self.provider = provider
        self.count = count
        self.cost = cost

class phoneDetails:
    def __init__(self, serviceDetail=None, phone=None, access_id=None, otp=None, status='Waiting', user='123456789'):
        self.serviceDetail = serviceDetail
        self.phone = phone
        self.access_id = access_id
        self.otp = otp
        self.status = status
        self.user = user

class Error:
    def __init__(self, message):
        self.message = message

    def __repr__(self) -> str:
        return self.message

class offers:
    def __init__(self, server, provider='Any', count=0, cost=0):
        self.server = server
        self.provider = provider
        self.count = int(count)
        self.cost = float(cost)

    def __repr__(self) -> str:
        return f"S({self.server}),P({self.provider}),Cost({self.cost}),Count({self.count})"

class priceResponse:
    def __init__(self, service:serviceInfo, offers:offers):
        self.service = service
        self.offers = offers

    def __repr__(self) -> str:
        return f"{self.service} has {self.offers}"
    
class phone_detail:
    def __init__(self,phone,access_id):
        self.phone = phone
        self.access_id = access_id
    def __repr__(self):
        return f"P({self.phone}), A({self.access_id})"