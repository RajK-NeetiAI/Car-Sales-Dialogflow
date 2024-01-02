import json
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

import config


def format_dialogflow_response(messages: list[str], output_contexts: list[dict] = []) -> dict:
    response_data = {}
    response_data['fulfillmentMessages'] = []
    response_data['fulfillmentMessages'].append(
        {
            'text': {
                'text': messages
            }
        }
    )
    if (len(output_contexts) > 0):
        response_data['outputContexts'] = output_contexts
    return response_data


def get_dialogflow_parameters(body: dict, context_name: str) -> dict:
    parameters = {}
    output_contexts = body['queryResult']['outputContexts']
    for oc in output_contexts:
        if context_name in oc['name']:
            parameters = oc['parameters']
    return parameters


def get_error_message():
    error_message = format_dialogflow_response([
        config.ERROR_MESSAGE
    ])
    return error_message


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, model=config.GPT_MODEL):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.OPENAI_API_KEY}',
    }
    json_data = {'model': model, 'messages': messages}

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=json_data
        )
        response = response.json()
        response = response['choices'][0]['message']['content']
        return response
    except Exception as e:
        print('Unable to generate ChatCompletion response')
        print(f'Exception: {e}')
        return config.ERROR_MESSAGE


def get_car_information(brand: str, model: str = None, fuel_type: str = None) -> dict:
    payload = {'brand': brand}
    if model is not None:
        payload.update({'model': model})
    if fuel_type is not None:
        payload.update({'fuel_type': fuel_type})
    try:
        response = requests.post(
            f'{config.BACKEND_URL}/api/get_filtered_channel_fast', json={"brand": "BMW"})
        response = response.json()
        car_data = []
        count = 3
        if response['ok']:
            for k, v in response['data'].items():
                if count == 0:
                    break
                count -= 1
                car_data.append({
                    'brandv': v['brand'],
                    'model': v['model'],
                    'price': v['price'],
                    'year': v['year'],
                    'mileage': v['mileage'],
                    'transmission': v['transmission']
                })

        return car_data
    except:
        return []


def get_openai_response(instruction: str) -> str:
    messages = []
    messages.append({'role': 'user', 'content': instruction})
    response = chat_completion_request(messages)

    return response


print(get_car_information('BMW'))
