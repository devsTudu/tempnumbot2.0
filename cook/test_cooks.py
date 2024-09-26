import pytest
import os
os.chdir(os.path.dirname(__file__))  # Set the working directory to the script's directory
pytest.main()

from helper import fastsms,tigersms,bowersms,server,fivesimsms
from models import phone_detail, offers
import time




test_cases = [(fastsms(),'aa','any'),
              (tigersms(),'aa','any'),
              (bowersms(),'amf','any'),
              (fivesimsms(),'acko','virtual21')]

@pytest.mark.parametrize("fs, service_code,provider", test_cases)
async def test_server(fs:server,service_code,provider):
        # Check balance
        balance = await fs.get_balance()
        assert isinstance(balance, float)
        assert balance > 0, "Insufficient balance"

        # Get prices
        prices = await fs.get_prices(service_code)
        assert isinstance(prices, list) and isinstance(prices[0],offers)
        for p in prices:
            assert p.cost > 0, "Invalid price"
            assert p.count > 0, "Invalid quantity"

        # Get phone number
        phone_number = await fs.get_phone_number(service_code,provider)
        assert isinstance(phone_number, phone_detail), "Error getting phone"
        
        # Check OTP status
        otp_status = await fs.check_otp(phone_number.access_id)
        assert isinstance(otp_status, str)
        assert otp_status == 'waiting', "OTP status is not 'waiting'"

        # Wait for OTP
        time.sleep(5)

        # Cancel service
        cancel_result = await fs.cancel(phone_number.access_id)
        assert isinstance(cancel_result, bool)
        assert cancel_result, "Cancellation failed"

