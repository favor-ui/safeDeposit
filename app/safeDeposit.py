#######################################################################
##################  IMPORTING LIBRARIES   ##############################
from app import app, mongo, api
from flask import Flask, jsonify, request, make_response
from flask_restful import Resource, Api, reqparse
import os, sys, re
from datetime import datetime, date, timedelta
import requests, json, uuid
from functools import wraps
from dotenv import load_dotenv

#######################################################################
##################  DEFINING DECORATOR FUNCTIONS  ##############################

# The actual decorator function
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.args.get('x-deposit-key') and request.args.get('x-deposit-key') == os.environ.get('DEPOSIT_KEY'):
            return view_function(*args, **kwargs)
        else:
            return make_response(jsonify({"message": "Unauthorized access at " + request.url, "status": False}), 403)
    return decorated_function

#######################################################################
##################  DEFINING FUNCTIONS   ##############################

@app.route('/', methods=['{POST', 'GET'])
def index():
    response= make_response('END connection ok')
    response.headers['Content-Type'] = "text/plain"
    return response

def nigerian_time():
    now = datetime.utcnow() + timedelta(hours=1)
    today = date.today()
    d2 = today.strftime("%B %d, %Y")
    tm = now.strftime("%H:%M:%S%p")
    return (d2 +' '+'at'+' '+tm)


def verify_agent(phone):
    head = {"key": "0987654321234567890"}
    data = {"phone_number": phone}
    res = requests.get('https://safe-payy.herokuapp.com/agent/verify', params=head, json=data)
    # print(json.loads(res.content)['status'])
    # print(json.loads(res.content))
    return res.json()

def verify_customer(phone):
    head = {"key": "0987654321234567890"}
    data = {"phone_number": phone}
    res = requests.get('https://safe-payy.herokuapp.com/customer/verify', params=head, json=data)
    # print(json.loads(res.content)['status'])
    # print(json.loads(res.content))
    return res.json()


def create_customer(phone):
    head = {"key": "0987654321234567890"}
    data = {
        'phone': phone
    }
    res = requests.post('https://safe-payy.herokuapp.com/customer/register', json=data, params=head)

    # print(json.loads(res.content)['status'])
    # print(json.loads(res.content))
    return res.json()


def make_payment(payer_phone, receiver_phone, amount):
    req_header = 'idl-7wqc9safepay _e7bccmw136f58'
    payload = {
        'payer_phone': payer_phone,
        'receiver_phone': receiver_phone,
        'amount': amount

    }
    res = requests.post('https://sspayment.herokuapp.com/payment?key={0}'.format(req_header), data=payload)
    return res.json()



#######################################################################
##################  DIFFERENT ENDPOINTS   ##############################

deposit = mongo.db.deposit
refs = str(uuid.uuid4().int)[:10]
# api route for Deposit
class Deposit(Resource):

    parser = reqparse.RequestParser()

    parser.add_argument('agent_phone',
                        type=str,
                        required=True,
                        help="agent_phone cannot be left blank")

    parser.add_argument('customer_phone',
                        type=str,
                        required=True,
                        help="customer_phone cannot be left blank")

    parser.add_argument('amount',
                        type=int,
                        required=True,
                        help="Amount must be number and cannot be left blank")

    def post(self):
        data = Deposit.parser.parse_args()

        # check if the length of phone number string or digits is upto 11 digits
        if len(data['agent_phone']) != 11 or len(''.join(i for i in data['agent_phone'] if i.isdigit())) != 11:
            return {"status": False, "error": "Agent phone must be 11 digits"}, 404

        elif len(data['customer_phone']) != 11 or len(''.join(i for i in data['customer_phone'] if i.isdigit())) != 11:
            return {"status": False, "error": "Customer phone must be 11 digits"}, 404

        elif data['agent_phone'] == data['customer_phone']:
            return {"status": False, "error": "Same phone numbers!"}, 404

        elif data["amount"] <= 0:
            return {"status": False, "error": "Enter a valid amount."}, 404

        # check to see that agent account exists in database, if not return error msg
        checkagent = verify_agent(data['agent_phone'])
        if not checkagent["status"]:
            return {"status": False, "error": "Agent account is not registered."}, 401

        # check to see that customer account exists in database, if not create it.
        checkcustomer = verify_customer(data['customer_phone'])
        if not checkcustomer["status"]:
            create_customer(data['customer_phone'])

        ## FOR PAYMENT. That is, debiting the PAYING ACCOUNT (AGENT)

        makepayment = make_payment(payer_phone=data['agent_phone'], receiver_phone=data['customer_phone'],
                                   amount=data["amount"])
        # returns {"status": True,"message": message} if True
        # or {"status": False, "error": error} if False
        if not makepayment["status"]:
            return (makepayment)

        # Time of transaction
        time = nigerian_time()

        # post transaction to payment collection and return the balance and success msg
        post = {"tran_reference": refs, "payer": data['agent_phone'], "receiver": data['customer_phone'], "amount": data['amount'],
                "time": time}

        message = "The cash deposit of NGN%s by %s was successful." % (data['amount'], data['customer_phone'])

        deposit.insert(post)
        return {"status": True, "payment": message}, 200

api.add_resource(Deposit, '/customer/deposit')


class DepositDetail(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('payer',
                        type=str,
                        required=True,
                        help="this field cannot be left blank")
    @require_appkey
    def get(self):
        # try:
        data = DepositDetail.parser.parse_args()
        phone2 = "".join(data['payer'].split())
        if not phone2:
            return {"status": False, "Error": " payer phone field cannot be empty."}, 404

        if len(phone2) != 11:
            return {"status": False, "Error": "Enter valid account lenght."}, 404


        find = deposit.find_one({"payer": phone2})
        if not find:
            return {"message": "Sorry no details was found for that account", "status": False}, 404

        output = []
        for q in deposit.find({"payer": phone2}):
            output.append({"Payer": q["payer"], "receiver": q['receiver'], "amount": q['amount'],
                           "Transaction time": q['time']})
        msg = "Transactions for {}".format(phone2)
        return jsonify({msg: output})

        # except Exception:
        #     return {"Message": "Invalid operation pls check and retry", "status":False}


api.add_resource(DepositDetail, '/deposit')


class DepositDetails(Resource):

    @require_appkey
    def get(self):
        # try:
        output = []
        for q in deposit.find():
            output.append({"Payer": q["payer"], "receiver": q['receiver'], "amount": q['amount'],
                           "Transaction time": q['time']})

        return jsonify({"All Transactions": output})

        # except Exception:
        #     return {"Message": "Invalid operation pls check and retry", "status": False}


api.add_resource(DepositDetails, '/all/deposit')
