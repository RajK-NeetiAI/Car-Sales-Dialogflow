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
