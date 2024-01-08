import re
import json
import random

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

import config


def format_dialogflow_response(message: str, output_contexts: list[dict] = []) -> dict:
    response_data = {}
    response_data['fulfillmentText'] = message
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


def get_openai_response(instruction: str) -> str:
    messages = []
    messages.append({'role': 'user', 'content': instruction})
    response = chat_completion_request(messages)

    return response


def replace_values(input_string: str, replacement_values: dict) -> str:
    pattern = r'\{.*?\}'

    def replace_match(match: re.Match):
        return replacement_values.get(match.group(0), match.group(0))
    output_string = re.sub(pattern, replace_match, input_string)

    return output_string


def get_response_from_responses_json(key_name: str, replacement_values: dict = None) -> str:
    with open('responses.json', 'r') as file:
        data = json.loads(file.read())
    response_data = data[key_name]
    if replacement_values is not None:
        response = replace_values(random.choice(
            response_data['responses']), replacement_values)
        return response
    else:
        return random.choice(response_data['responses'])
