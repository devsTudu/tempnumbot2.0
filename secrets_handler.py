import os
from dotenv import load_dotenv
required_secrets = [
    # General
    'BOT_TOKEN',
    'POSTGRESQL_DB',
    'PROFIT_RATE',
    #Cook - Server Realted
    'FASTSMS_API',
    'FIVESIM_API',
    'TIGER_API',
    'BOWER_API',
    # Reception - Bank Related
    'BHARATPE_MERCHANT_ID',
    'BHARATPE_TOKEN'
]

VARIABLES = {}

def check_required_secrets():
    load_dotenv()
    for variable in required_secrets:
        secret = os.environ.get(variable)
        if not secret:
            secret = input(f"Enter {variable}:")
        VARIABLES[variable] = secret
