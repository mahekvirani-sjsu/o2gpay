from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_cors import CORS
from datetime import datetime
import json
import logging
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PaymentResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    request_type = db.Column(db.String(50))  
    response_json = db.Column(db.JSON)  


with app.app_context():
    db.create_all()


def store_payment_response(request_type, response_data):
    payment_response = PaymentResponse(
        request_type=request_type,
        response_json=response_data
    )
    db.session.add(payment_response)
    db.session.commit()
    return payment_response.id 
@app.route('/payment/responses', methods=['GET'])
def view_payment_responses():
    responses = PaymentResponse.query.all()
    result = [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "request_type": r.request_type,
            "response_json": r.response_json
        }
        for r in responses
    ]
    return jsonify(result), 200
# Serve index.html
@app.route('/')
def index():
    return render_template('index.html')

def create_headers():
    return {
        'Authorization': 'Basic MGY2ZDI4ZmYtZWJmMi00ZjRlLWEzZTItZjk0ZTJmMmMxMmM3OmZjRGJYUFJSRVdwZFJ4c2pwcFFydk1RaHdhc3lKdXhYTUJtbw==',
        'x-site-entity-id': '4c6664c7-733e-4d12-a75c-9796a59c9fd8',
        'Content-Type': 'application/json',
       
    }


@app.route('/payment/poscloud/nexo/payment', methods=['POST'])
def handle_payment():
    data = request.get_json()
    amount = data.get('amount')

    if not amount:
        return jsonify({"error": "Amount is required"}), 400

    url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/payment'

    headers = {
        'Authorization': 'Basic MGY2ZDI4ZmYtZWJmMi00ZjRlLWEzZTItZjk0ZTJmMmMxMmM3OmZjRGJYUFJSRVdwZFJ4c2pwcFFydk1RaHdhc3lKdXhYTUJtbw==',
        'x-site-entity-id': '4c6664c7-733e-4d12-a75c-9796a59c9fd8',
        'Content-Type': 'application/json',
        'Amount-Header': amount  
    }

    post_data = {
        "MessageHeader": {
            "MessageClass": "SERVICE",
            "MessageCategory": "PAYMENT",
            "MessageType": "REQUEST",
            "ServiceID": "VERIFONE",
            "SaleID": "VERIFONE",
            "POIID": "807-766-588"
        },
        "PaymentRequest": {
            "SaleData": {
                "OperatorID": "VERIFONE",
                "SaleTransactionID": {
                    "TransactionID": "VERIFONE",
                    "TimeStamp": "2020-04-20T14:43:59+05:30"
                }
            },
            "PaymentTransaction": {
                "AmountsReq": {
                    "Currency": "USD",
                    "RequestedAmount": amount
                }
            },
            "PaymentData": {
                "PaymentType": "NORMAL",
                "SplitPaymentFlag": ""
            }
        }
    }

    try:
        response = requests.post(url, json=post_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
             # Store the payment response in the database
            response_id = store_payment_response(request_type="PAYMENT", response_data=result)
            return jsonify({"result": result, "db_id": response_id}), 200
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/payment/poscloud/nexo/ebt', methods=['POST'])
def handle_ebt_payment():
    
    data = request.get_json()
    amount = data.get('amount')


    if not amount:
        return jsonify({"error": "Amount is required"}), 400


    url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/payment'


    headers = {
    'Authorization': "Basic MGY2ZDI4ZmYtZWJmMi00ZjRlLWEzZTItZjk0ZTJmMmMxMmM3OmZjRGJYUFJSRVdwZFJ4c2pwcFFydk1RaHdhc3lKdXhYTUJtbw==",
    'x-site-entity-id': '4c6664c7-733e-4d12-a75c-9796a59c9fd8',
    'Content-Type': 'application/json'
    }


    post_data = {
        "MessageHeader": {
            "MessageClass": "SERVICE",
            "MessageCategory": "PAYMENT",
            "MessageType": "REQUEST",
            "ServiceID": "VERIFONE",
            "SaleID": "VERIFONE",
            "POIID": "807-766-588"
        },
        "PaymentRequest": {
            "SaleData": {
                "SaleTransactionID": {
                    "TransactionID": "VERIFONE",
                    "TimeStamp": "2019-08-21T16:35:05.073Z" 
                },
                "CustomerOrderReq": None,
                "SaleToAcquirerData": None
            },
            "PaymentTransaction": {
                "AmountsReq": {
                    "Currency": "USD",
                    "RequestedAmount": amount,
                    "TipAmount": "0.00"
                },
                "TransactionConditions": {
                    "VF_RequestedPaymentType": "EBT"
                }
            },
            "PaymentData": {
                "PaymentType": "REFUND"
            }
        }
    }

    try:
       
        response = requests.post(url, json=post_data, headers=headers)

        if response.status_code == 200:
          
            result = response.json()
            response_id = store_payment_response(request_type="PAYMENT", response_data=result)
            return jsonify({"result": result, "db_id": response_id}), 200
            
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
   
        return jsonify({"error": str(e)}), 500

@app.route('/payment/reversal', methods=['POST'])
def handle_reversal():
    data = request.get_json()
    last4Digits = data.get('last4Digits')
    
    if not last4Digits:
        return jsonify({"error": "Last 4 digits are required"}), 400


    url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/v2/reversal'

    post_data = {
       "MessageHeader": {
        "MessageClass": "SERVICE",
        "MessageCategory": "REVERSAL",
        "MessageType": "REQUEST",
        "ServiceID": "VERIFONE",
        "SaleID": "VERIFONE",
        "POIID": "807-766-588"
    },
    "ReversalRequest": {
        "SaleData": {
            "SaleTransactionID": {
                "TransactionID": "VERIFONE",
                "TimeStamp": "2021-02-25T07:42:12.580Z"
            },
            "CustomerOrderReq": [
                "BOTH"
            ],
            "SaleToPOIData": json.dumps({
                        "c": last4Digits,
                        "m": "MC",
                        "p": "DEBIT",
                        "i": "2222224",
                        "r": "CAPTURED",
                        "rc": "4",
                        "ts": "SUCCESS"
                    })},
        "OriginalPOITransaction": {
            "SaleID": "VERIFONE",
            "POIID": "807-766-588",
            "POITransactionID": {
                "TransactionID": "3663",
                "TimeStamp": "2021-02-25T07:42:12.580Z"
            }
        },
        "ReversalReason": "CUSTCANCEL",
        "CustomerOrder": {
            "CustomerOrderID": "VERIFONE",
            "StartDate": "2021-02-25T07:42:12.580Z",
            "ForecastedAmount": 1.00,
            "OpenOrderState": True,
            "Currency": "USD"
        }
    }
    }

    try:
  
        headers = create_headers()
        response = requests.post(url, json=post_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            response_id = store_payment_response(request_type="PAYMENT", response_data=result)
            return jsonify({"result": result, "db_id": response_id}), 200
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
       
        return jsonify({"error": str(e)}), 500
@app.route('/payment/refund', methods=['POST'])
def handle_refund():
    data = request.get_json()
    amount = data.get('refundDetails')
    if not amount:
        return jsonify({"error": "Amount is required"}), 400

    url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/payment'

   
    headers = create_headers()

    
    post_data = {
        "MessageHeader": {
            "MessageClass": "SERVICE",
            "MessageCategory": "PAYMENT",
            "MessageType": "REQUEST",
            "ServiceID": "VERIFONE",
            "SaleID": "VERIFONE",
            "POIID": "807-766-588"
        },
        "PaymentRequest": {
            "SaleData": {
                "OperatorID": "VERIFONE",
                "SaleTransactionID": {
                    "TransactionID": "VERIFONE",
                    "TimeStamp": "2020-04-20T14:43:59+05:30"
                }
            },
            "PaymentTransaction": {
                "AmountsReq": {
                    "Currency": "USD",
                    "RequestedAmount": amount
                }
            },
            "PaymentData": {
                "PaymentType": "REFUND",
                "SplitPaymentFlag": ""
            }
        }
    }

    try:
        response = requests.post(url, json=post_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            response_id = store_payment_response(request_type="PAYMENT", response_data=result)
            return jsonify({"result": result, "db_id": response_id}), 200
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/payment/ebt/refund', methods=['POST'])
def handle_ebt_refund():
    try:
 
        data = request.get_json()

        
        if not data or 'refundAmount' not in data :
            return jsonify({"error": "Refund amount and last 4 digits are required"}), 400

        refund_amount = data.get('refundAmount')

     
        url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/payment'


        post_data = {
            "MessageHeader": {
                "MessageClass": "SERVICE",
                "MessageCategory": "PAYMENT",
                "MessageType": "REQUEST",
                "ServiceID": "VERIFONE",
                "SaleID": "VERIFONE",
                "POIID": "807-766-588"
            },
            "PaymentRequest": {
                "SaleData": {
                    "SaleTransactionID": {
                        "TransactionID": "VERIFONE",
                        "TimeStamp": "2019-08-21T16:35:05.073Z"
                    },
                    "CustomerOrderReq": None,
                    "SaleToAcquirerData": None
                },
                "PaymentTransaction": {
                    "AmountsReq": {
                        "Currency": "USD",
                        "RequestedAmount":refund_amount ,
                        "TipAmount": "0.00"
                    },
                    "TransactionConditions": {
                        "VF_RequestedPaymentType": "EBT"
                    }
                },
                "PaymentData": {
                    "PaymentType": "REFUND"
                }
            }
        }
 
        headers = create_headers()
        response = requests.post(url, json=post_data, headers=headers)
        print(response)
        if response.status_code == 200:
            result = response.json()
            response_id = store_payment_response(request_type="PAYMENT", response_data=result)
            return jsonify({"result": result, "db_id": response_id}), 200
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/payment/balanceInquiry', methods=['POST'])
def handle_balance_inquiry():
    try:
 
        post_data = {
            "MessageHeader": {
                "MessageClass": "SERVICE",
                "MessageCategory": "BALANCEINQUIRY",
                "MessageType": "REQUEST",
                "ServiceID": "VERIFONE",
                "SaleID": "VERIFONE",
                "POIID": "807-766-588"
            },
            "BalanceInquiryRequest": {}
        }


        url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/v2/balanceInquiry'

        headers = create_headers()
        response = requests.post(url, json=post_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return jsonify(result), 200
        else:
            return jsonify({"error": f"HTTP error: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=8000)
