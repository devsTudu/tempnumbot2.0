#Waiter End Point that interacts with Telegram Bot API

from secrets_handler import check_required_secrets
check_required_secrets()

from flask import Flask, request, Response
from waiter import main as waiter
from waiter.helper import report_reception,report_balance
from telegram.bot import logger

import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "The End Point is running"

@app.route('/bot',methods=['POST','GET'])
def bot():
    if request.method == 'POST':
        data = request.get_json()
        try:
            thread = threading.Thread(target=waiter.workOn,args=(data,))
            thread.start()
        except Exception as e:
            logger.warning("Invalid request from Telegram")
            print(data)
        finally:
            return "Request Processed"
    else:
        print("Working from url :",request.base_url)
        return "<h1>Server is Working Fine</h1>"

@app.route('/resethook')
def resethook():
    return waiter.setWebhook(request.base_url)

@app.route('/setmanualhook')
def manualset():
    url = request.args.get('url')
    if not url:
        return "url parameter not received"
    return waiter.setmanualhook(url)

@app.route('/checkreport')
def check_report():
    return Response([report_balance(),report_reception()])


if __name__=='__main__':
    app.run(debug=True,port=5000)

