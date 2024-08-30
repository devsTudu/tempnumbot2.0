import os
from dotenv import load_dotenv
required_secrets = [
    'BOT_TOKEN',
    'COOK_API_TOKEN',
    'POSTGRESQL_DB',
    'USE_LITE_DB'
]



def check_required_secrets():
    load_dotenv()
    for variable in required_secrets:
        if not os.environ.get(variable):
            secret = input(f"Enter {variable}:")
            os.environ[variable] = secret
