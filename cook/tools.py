from json import JSONDecodeError
import json
from os import getcwd,path
from typing import Union

from requests import get
from .models import (serviceInfo, countryInfo, Error)
from secrets_handler import VARIABLES

# Variable Declaration
BASE_URL = {
    "fast": "https://fastsms.su/stubs/handler_api.php",
    "bower": "https://smsbower.com/stubs/handler_api.php",
    "tiger": "https://api.tiger-sms.com/stubs/handler_api.php?",
}

TOKENS = {
    'fast': VARIABLES['FASTSMS_API'],
    'bower': VARIABLES['BOWER_API'],
    'tiger': VARIABLES['TIGER_API'],
    '5Sim': VARIABLES['FIVESIM_API']
}


# Common Functions for Requesting Data from API

class commonTools:
    def __init__(self) -> None:
        module_dir = path.dirname(__file__)
        menu = "menuList.json"
        menu_path = path.join(module_dir, menu)

        with open(menu_path, 'r') as file:
            data = json.load(file)
        self.serviceMenu = data

    def getKeys(self, serviceName: str):
        if serviceName in self.serviceMenu:
            return self.serviceMenu[serviceName]
        else:
            return None

    def getServiceInfo(self, serviceName: str, country: countryInfo) -> serviceInfo:
        keys = self.getKeys(serviceName)
        if keys:
            return serviceInfo(name=serviceName, country=country, **keys)

    @staticmethod
    def isError(obj) -> bool:
        if isinstance(obj, str):
            return obj.startswith('Error')
        elif isinstance(obj, dict):
            return obj.keys() == {'Error'}
        elif isinstance(obj, Error):
            return True
        else:
            return False

    @staticmethod
    def getText(url, params=None, headers=None) -> str:
        """
        Returns the text of the response from the request if successfully,
        Otherwise Error(code)(response)
        """
        resp = get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            return "Error" + str(resp.status_code) + resp.text

    @staticmethod
    def getJson(url, params=None, headers=None, responsePrint=False) -> dict:
        """
        Return Json Object if successfully, else a {'Error':response.Text}
        """
        resp = get(url, params=params, headers=headers)

        if resp.status_code == 200:
            if responsePrint:
                print(resp.content)
            try:
                if resp.json() == {}:
                    return {"Error": "Empty JSON response"}
                return resp.json()
            except JSONDecodeError as j:
                return {'Error': str(j)}
        else:
            return {"Error": resp.text}

    def getCountryNameFromCode(self, code: str) -> Union[str, None]:
        """Returns the country name from the code, or None if
        no country name was found"""
        if code == '22':
            return 'india'
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getCountries"}
        data_country = self.getJson(url, params=param)
        if not self.isError(data_country):
            return data_country[str(code)]
        else:
            return None

    def getServiceNameFromCode(self, code: str) -> Union[str, None]:
        """Returns the Service Name from the code, or None if
        no Service name was found"""
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getServices"}
        data = self.getJson(url, params=param)
        if not self.isError(data):
            return data[str(code)]
        else:
            return None
