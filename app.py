import os

from flask import Flask, jsonify, render_template, request, send_from_directory

from utils import format_dialogflow_response
from action import *

app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='images/favicon.png')


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/dialogflow', methods=['POST'])
def dialogflow():
    body = request.get_json()
    try:
        action = body['queryResult']['action']
    except:
        action = ''
    query = body['queryResult']['queryText']
    session_id = body['session']
    response_data = {}

    print(f'{action} -> {query}')

    if action == 'defaultWelcomeIntent':
        response_data = handle_default_welcome_intent(body)
    elif action == 'buyACar':
        response_data = handle_buy_a_car(body)
    elif action == 'userProvidesModel':
        response_data = handle_user_provides_model(body)
    elif action == 'userConfirmsDetailsOverWhatsapp':
        response_data = handle_user_confirms_details_over_whatsapp(body)
    elif action == 'userDeniesDetailsOverWhatsapp':
        response_data = handle_user_denies_details_over_whatsapp(body)
    elif action == 'userDeniesModel':
        response_data = handle_user_denies_model(body)
    elif action == 'sellACar':
        response_data = handle_sell_a_car(body)
    elif action == 'orderStatus':
        response_data = handle_order_status(body)
    elif action == 'userProvidesOrderNumber':
        response_data = handle_user_provides_order_number(body)
    elif action == 'userProvidesBrand':
        response_data = handle_user_provides_brand(body)
    else:
        response_data = format_dialogflow_response(
            [body['queryResult']['fulfillmentText']])

    response = response_data['fulfillmentText']

    print(response)

    add_conversation(query, response, session_id)

    return jsonify(response_data)
