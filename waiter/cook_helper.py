import pytest

from cook.models import phone_detail, priceResponse
from telegram.bot import logger
from os import path
from cook import main as cook_local
from dotenv import load_dotenv
from secrets_handler import VARIABLES
import json

from requests import get

load_dotenv()
MENU_LIST = path.join(path.dirname(path.realpath(__file__)), "menu.txt")
PROFIT_RATE = int(VARIABLES['PROFIT_RATE']) if VARIABLES['PROFIT_RATE'] else 30
SALES_PRICE = lambda x: int(float(x) * (1 + PROFIT_RATE / 100) + 1)
TEMPLATES = path.join(path.dirname(__file__), "templates")


class cookAPI:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_serviceList() -> list:
        """Returns the list of services available, from the cook api"""
        with open("cook\\menuList.json",'r') as file:
            data = json.load(file)
            menu = list(data.keys())
        return menu

    @classmethod
    def get_server_list(cls, service_name) -> list[dict]:

        """Returns the json list of all the servers, available for the service_name, else returns none"""
        prices = cook_local.get_price_from_name(service_name)
        if isinstance(prices, priceResponse):
            return map(vars, prices.offers)
        else:
            logger.error(f"Error fetching offers for {service_name}")
            return []

    @classmethod
    def get_phone_no(cls, server, service_name, provider):
        """Returns dict{phone,access_id,server}"""
        phone = cook_local.get_phone_number(server=server, service_name=service_name, provider=provider)
        if isinstance(phone, phone_detail):
            try:
                data = {
                    'phone': phone.phone,
                    'access_id': phone.access_id,
                    'server': server
                }
                return data
            except KeyError as k:
                msg = f"Error fetching number,{k}"
                logger.fatal(msg)

    @classmethod
    def check_for_otp(cls, server, access_id):
        """returns otp if received, 0 if waiting, -1 otherwise"""
        update = cook_local.get_updates(server, access_id)
        if isinstance(update, str):
            if 'wait' in update:
                return 0
            if 'cancel' in update:
                return -1
            return update

    @classmethod
    def cancel_phone(cls, server, access_id):
        iscanceled = cook_local.cancel_phone(server, access_id)
        if not iscanceled:
            logger.warning(f"Error canceling @ {server} , {access_id}")
        return iscanceled


def encodeList(lis) -> dict:
    """Returns the dictionary with unique 7 char key for the service name"""
    import hashlib
    name_dict = {}
    for name in lis:
        name = name.strip()
        hash_object = hashlib.sha256(name.encode())
        key = hash_object.hexdigest()[:7]  # Hash and truncate to 7 characters
        name_dict[key] = name
    return name_dict


class serviceOperation:
    def __init__(self, file_address: str = MENU_LIST):
        self.file_address = file_address

        def read_menu():
            with open(file_address, 'r', encoding="utf-8") as file:
                lis = file.readlines()
            return encodeList(lis)

        def updateAllDetails():
            """Download the Menu, and make the database"""
            lis = cookAPI().get_serviceList()
            with open(self.file_address, 'w', encoding='utf-8') as file:
                for i in lis:
                    file.write(i + '\n')
            self.database = encodeList(lis)

        def updatePages():
            menu = self.database
            service_list = []
            for i in menu:
                service = "➤" + (menu[i].replace('.', ' .')) + " /ser_" + i
                service_list.append(service)

            # Number of chunks
            num_chunks = 15

            # Ensure chunk size divides the number of rows evenly
            chunk_size = len(service_list) // num_chunks

            # Iterate through chunks
            for i in range(num_chunks):
                start_index = i * chunk_size
                end_index = (i + 1) * chunk_size
                # Get the current chunk of data as DataFrame
                if i != num_chunks - 1:
                    chunk_df = service_list[start_index:end_index]
                else:
                    chunk_df = service_list[start_index:]
                data_to_load = chunk_df

                # Export the chunk to a txt file, converting DataFrame to string representation
                with open(path.join(TEMPLATES , f"page{i + 1}.txt"), "w", encoding='utf-8') as f:
                    f.write("\n".join(data_to_load))

        if not path.isfile(file_address):
            logger.log(1, "Menu data Updating from Cook")
            updateAllDetails()
            updatePages()

        else:
            self.database = read_menu()

    def fuzzy_search(self, query_term, threshold=80):
        """
      Performs a fuzzy search on a list of service names based on a query term.

      Args:
          service_names (list): A list of service names (strings).
          query_term (str): The term to search for.
          threshold (int, optional): The minimum Levenshtein distance similarity score (0-100). Defaults to 80.

      Returns:
          list: A list of service names with a Levenshtein distance below the threshold from the query term.
      """

        def levenshtein(str1, str2):
            """
          Calculates the Levenshtein distance between two strings.

          This function calculates the minimum number of single-character edits (insertions, deletions, replacements)
          needed to transform one string into another.

          Args:
              str1 (str): The first string.
              str2 (str): The second string.

          Returns:
              int: The Levenshtein distance between the strings.
          """
            n_m = len(str1) + 1
            d = [[0 for _ in range(n_m)] for _ in range(len(str2) + 1)]

            for i in range(1, n_m):
                d[0][i] = i

            for j in range(1, len(str2) + 1):
                d[j][0] = j

            for j in range(1, len(str2) + 1):
                for i in range(1, n_m):
                    if str1[i - 1] == str2[j - 1]:
                        cost = 0
                    else:
                        cost = 1
                    d[j][i] = min(d[j - 1][i] + 1, d[j][i - 1] + 1,
                                  d[j - 1][i - 1] + cost)

            return d[-1][-1]

        matches = []
        for code, name in list(self.database.items()):
            distance = levenshtein(query_term.lower(),
                                   name.lower())
            similarity = ((len(query_term) - distance) / len(query_term)) * 100
            if (similarity >= threshold) or (query_term.lower() in name.lower()):
                matches.append([similarity, name, code])
        match_ordered = sorted(matches, key=lambda row: row[0], reverse=True)
        if len(matches) == 0:
            return "Not found"
        return match_ordered

    def getServiceName(self, service_code) -> str:
        if service_code in self.database:
            return self.database[service_code]

    @staticmethod
    def getServerListButtonFor(service_name) -> list[list]:
        """Returns the list of servers available for the given service code"""
        # service_name = self.database[service_code]
        lis = cookAPI().get_server_list(service_name=service_name)
        try:
            # return sorted(dicts, key=lambda x: x[key])
            lis = sorted(lis, key=lambda x: x['cost'])
        except:
            pass
        buttons = []
        if lis:
            for i, offer in enumerate(lis):
                btn = [(f"🌐SERVER {i + 1} with cost:{SALES_PRICE(offer['cost'])}💰",
                        f"buy_{offer['server']}_{service_name}_{offer['provider']}")]
                buttons.append(btn)
        return buttons

    @staticmethod
    def fetchPrice(server, service_name, provider) -> float:
        lis = cookAPI().get_server_list(service_name=service_name)
        for i in lis:
            if i['server'] == server and i['provider'] == provider:
                return SALES_PRICE(i['cost'])
        logger.critical(f"Error price fetching,{server, service_name, provider}")
        return 9999

    @staticmethod
    def getPhoneNumber(service_name: str, server: str, provider: str = 'Any'):
        """Use the Cook API to fetch the phone number and access_id"""
        if server not in ['Fast', 'Tiger', '5Sim', 'Bower']:
            raise Exception("Invalid Server used to fetch phone number")
        else:
            return cookAPI().get_phone_no(server, service_name, provider)

    @staticmethod
    def getOTP(server, actCode):
        """Make API Calls to get the OTP, return -1 if canceled, 0 for waiting, and otp if sucess"""
        return cookAPI().check_for_otp(server=server, access_id=actCode)

    @staticmethod
    def cancelPhone(server, access_id) -> bool:
        """Returns True if successfully canceled"""
        return cookAPI().cancel_phone(server, access_id)

    @staticmethod
    def list_items_with_commands(service_lis: list[str]) -> str:
        encoded = encodeList(service_lis)
        resp = "".join(f"\n/ser_{code} {name}" for code, name in encoded.items())
        return resp


serviceOps = serviceOperation()


class testCases:

    def __init__(self, service: serviceOperation) -> None:
        self.x = service

    def test_fuzzysearch(self):
        for _ in range(5):
            q = input("Enter term:")
            p = int(input("Enter power:"))
            y = self.x.fuzzy_search(q, p)
            print(y)

    def test_see_price(self):
        for _ in range(5):
            s = input("Enter the name:")
            p = input("Provider:")
            ser = input("server :")
            try:
                print(self.x.fetchPrice(server=ser, service_name=s, provider=p))
            except KeyError:
                print("Wrong Key")


server_operations = [
    ('Fast', 'Any', 'Probo'),
    ('Tiger', 'Any', 'Probo'),
    ('5Sim', 'virtual21', 'Alipay'),
]


@pytest.mark.parametrize('server, provider, name', server_operations)
def test_operations(server, provider, name):
    buttons = serviceOps.getServerListButtonFor(name)
    print(buttons)
    assert isinstance(buttons, list)

    price = serviceOps.fetchPrice(server, name, provider)
    assert isinstance(price, int), "Fetching Price"

    # Get phone number
    phone = serviceOps.getPhoneNumber(name, server, provider)
    assert isinstance(phone, dict), "Generating Phone Number"

    if isinstance(phone, phone_detail):
        print(phone)
        update = serviceOps.getOTP(server, phone.access_id)
        print(update)
        assert isinstance(update, int), "Fetching OTP"

        cancel = serviceOps.cancelPhone(server, phone.access_id)
        assert isinstance(cancel, bool), "Cancelling Phone"
        assert cancel, "Couldnot cancel"


if __name__ == '__main__':
    testCases(serviceOps).test_see_price()
