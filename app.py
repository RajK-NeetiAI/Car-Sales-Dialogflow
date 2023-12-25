from flask import Flask, jsonify, request

from utils import format_dialogflow_response
from action import *

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({'message': 'Application is running.'})


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

    if action == 'buyACar':
        response_data = handle_buy_a_car(body)
    elif action == 'userProvidesBuyOption':
        response_data = handle_user_provides_buy_option(body)
    elif action == 'confirmAction':
        response_data = handle_confirm_action(body)
    elif action == 'denyAction':
        response_data = handle_deny_action(body)
    elif action == 'userProvidesName':
        response_data = handle_user_provides_name(body)
    elif action == 'userProvidesMobile':
        response_data = handle_user_provides_mobile(body)
    elif action == 'sellACar':
        response_data = handle_sell_a_car(body)
    else:
        response_data = format_dialogflow_response(
            [body['queryResult']['fulfillmentText']])

    response = response_data['fulfillmentMessages'][0]['text']['text'][0]

    add_conversation(query, response, session_id)

    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True)
