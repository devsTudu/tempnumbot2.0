import datetime
from symbol import encoding_decl
from telegram.bot import logger
from telegram.models import phoneNumberFlow
from os import getenv, path

from dotenv import load_dotenv

from requests import get

load_dotenv()
API_KEY = getenv("COOK_API_TOKEN")
COOK_URL = "https://fastapi-tempnumbot.onrender.com"
MENU_LIST = "menu.txt"

class cookAPI:
    headers = {
      'accept': 'application/json',
      'x-api-key': API_KEY
    }
    
    @staticmethod
    def get_serviceList()->list:
        """Returns the list of services available, from the cook api"""
        data = get(COOK_URL+"/downloadList")
        menu = list(data.json().keys())
        return menu

    @classmethod
    def get_server_list(cls,service_name)->list[dict]:
        """Returns the json list of all the servers, available for the service_name, else returns none"""
        url = f"{COOK_URL}/getPrices"
        params = {'servicename':service_name}
    
        response = get(url,params=params,headers=cls.headers)
        if response.status_code == 200:
            reply :list[dict] = response.json()['offers']
            return reply
        else:
            logger.error(f"Error fetching offers for {service_name},returned {response.text}")
            return []
            

    @classmethod
    def get_phone_no(cls,server,service_name,provider):
        """Returns dict{phone,access_id,server}"""
        url = COOK_URL+'/getPhone'
        params = {'server':server,'service_name':service_name,'provider':provider}
        response = get(url,params,headers=cls.headers)

        if response.status_code == 200:
            try:
                data = {
                    'phone':response.json()['phone'],
                    'access_id':response.json()['access_id'],
                    'server':server
                }
                return data
            except KeyError as k:
                msg = f"Error fetching number,{k}"
                logger.fatal(msg)

       
    @classmethod
    def check_for_otp(cls,server,access_id):
        """returns otp if received, 0 if waiting, -1 otherwise"""
        url = COOK_URL+'/updates'
        params = {'server':server,'access_id':access_id,'phone':'9348692623'}
        response = get(url,params,headers=cls.headers)
        print(params)
        print(response)
        if response.status_code == 200:
            try:
                status = response.json()['status']
                if status == "Success":
                    return response.json()['otp']
                elif status == 'Waiting':
                    return 0
                else:
                    return -1
            except KeyError as k:
                msg = f"Error fetching otp for {server} with id {access_id} : {k}"
                logger.fatal(msg)
        print(response.text)
        return 0
    
    @classmethod
    def cancel_phone(cls,server,access_id):
        url = COOK_URL+'/cancelPhone'
        params = {'server':server, 'access_id':access_id}
        response = get(url,params,headers=cls.headers)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Error canceling @ {server} , {access_id}")
               
        

def encodeList(lis)->dict:
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
            with open(file_address,'r',encoding="utf-8") as file:
                lis = file.readlines()
            return encodeList(lis)

        def updateAllDetails():
            """Download the Menu, and make the database"""
            lis = cookAPI().get_serviceList()
            with open(self.file_address,'w',encoding='utf-8') as file:
              for i in lis:
                file.write(i+'\n')
            self.database = encodeList(lis)

        def updatePages():
            menu = self.database
            service_list = []
            for i in menu:
                service = "➤" + (menu[i].replace('.',' .')) + " /ser_" +i
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
                with open(f"templates/page{i+1}.txt", "w",encoding='utf-8') as f:
                    f.write("\n".join(data_to_load))
        
        if not path.isfile(file_address):
            logger.log(1,"Menu data Updating from Cook")
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
        for code,name in list(self.database.items()):
            distance = levenshtein(query_term.lower(),
                                        name.lower())
            similarity = ((len(query_term) - distance) / len(query_term)) * 100
            if similarity >= threshold:
                matches.append([similarity,name,code])
        match_ordered = sorted(matches,key=lambda row:row[0],reverse=True)
        if len(matches) == 0:
            return "Not found"
        return match_ordered


    def getServiceName(self,service_code)->str:
        if service_code in self.database:
            return self.database[service_code]
    
    def getServerListButtonFor(self,service_name)->list[list]:
        """Returns the list of servers available for the given service code"""
        # service_name = self.database[service_code]
        lis = cookAPI().get_server_list(service_name=service_name)
        buttons = []
        if lis:
            for i in lis:
                btn = [(f"{i['server']}🌐 with cost:{i['cost']}💰",
                       f"buy_{i['server']}_{service_name}_{i['provider']}")]
                buttons.append(btn)
        return buttons
    
    @staticmethod
    def fetchPrice(server,service_name,provider)->float:
        lis = cookAPI().get_server_list(service_name=service_name)
        for i in lis:
            if i['server']==server and i['provider'] == provider:
                return float(i['cost'])
        logger.critical(f"Error price fetching,{server,service_name,provider}")
        return 99.9
        
    @staticmethod
    def getPhoneNumber(service_name:str,server:str,provider:str='Any'):
        """Use the Cook API to fetch the phone number and access_id"""
        if server not in ['Fast', 'Tiger', '5Sim', 'Bower']:
            raise Exception("Invalid Server used to fetch phone number")
        else:
            return cookAPI().get_phone_no(server,service_name,provider)
           
            
    @staticmethod
    def getOTP( server,actCode):
        """Make API Calls to get the OTP, return -1 if canceled, 0 for waiting, and otp if sucess"""
        return cookAPI().check_for_otp(server=server,access_id=actCode)

    @staticmethod
    def cancelPhone(server,access_id)->bool:
        """Returns True if successfully canceled"""
        return cookAPI().cancel_phone(server,access_id) == 'true'

    @staticmethod
    def list_items_with_commands(service_lis:list[str])->str:
        encoded = encodeList(service_lis)
        resp = "\n".join(f"/ser_{code} {name}"for code,name in encoded.items())
        return resp


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
                print(self.x.fetchPrice(server=ser,service_name=s,provider=p))
            except KeyError:
                print("Wrong Key")
    def checkUTR(self):
        x = getRecharge(input())
        print(x)


serviceOps = serviceOperation()

if __name__ == '__main__':
    service = serviceOperation()
    