from fuzzywuzzy import process
from utils import *
from database import *


def handle_default_welcome_intent(body: dict) -> dict:
    session = body['session']
    fulfillment_message = body['queryResult']['fulfillmentMessages'][0]['text']['text'][0]
    response = get_openai_response(f'''Please format the following sentence in a polite tone. \
SENTENCE: {fulfillment_message}''')
    brand_data = get_brand_information()
    output_contexts = []
    output_contexts.append(
        {
            'name': f'{session}/contexts/session-vars',
            'lifespanCount': 50,
            'parameters': {
                'brand_data': brand_data
            }
        }
    )

    return format_dialogflow_response([response], output_contexts)


def handle_buy_a_car(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    if 'brand_data' not in parameters.keys():
        brand_data = get_brand_information()
        parameters.update({'brand_data': brand_data})
    if parameters['car_company'] == '':
        '''TODO
        [ ] We can apply fuzzywuzzy here
        '''
        print('No car brand in the query.')
    else:
        '''Car brand found
        '''
        brand_data = parameters['brand_data']
        brand = None
        processed = process.extractOne(
            parameters['car_company'].upper(), brand_data)
        brand = processed[0]
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-car-model',
                'lifespanCount': 1
            }
        )
        output_contexts.append(
            {
                'name': f'{session}/contexts/session-vars',
                'lifespanCount': 50,
                'parameters': {
                    'brand_data': brand_data,
                    'brand': brand
                }
            }
        )
        response = get_response_from_responses_json(
            'car_brand_found', {"{brand}": brand})

    return format_dialogflow_response([response], output_contexts)


def handle_user_provides_model(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    model_data = get_model_information(brand)
    if parameters['car_model'] == '':
        '''TODO
        [ ] We can apply fuzzywuzzy here
        '''
        print('No car model in the query.')
    else:
        processed = process.extractOne(parameters['car_model'], model_data)
        model = processed[0]
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/session-vars',
                'lifespanCount': 50,
                'parameters': {
                    'model_data': model_data,
                    'model': model
                }
            }
        )
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-action',
                'lifespanCount': 1
            }
        )
        response = get_response_from_responses_json(
            'car_model_found', {"{brand}": brand, "{model}": model})

    return format_dialogflow_response([response], output_contexts)


def handle_user_confirms_details_over_whatsapp(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    model = parameters['model']
    '''User mobile number
    '''
    print(body['originalDetectIntentRequest']['payload'])
    car_data = get_car_information(brand, model)
    print(car_data)
    '''TODO
    [ ] format the car data
    [ ] send the car data to the WhatsApp
    '''
    '''User wants to receive the details over WhatsApp
    '''
    response = get_response_from_responses_json('send_car_data_whatsapp')

    return format_dialogflow_response([response])


def handle_user_denies_details_over_whatsapp(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    model = parameters['model']
    car_data = get_car_information(brand=brand, model=model)
    response = f'We have the following {brand} {model} cars available:\n'
    for cd in car_data:
        response += get_response_from_responses_json(
            'do_not_car_data_whatsapp',
            {'{brand}': cd['brand'], '{model}': cd['model'], '{price}': int(cd['price']), '{year}': int(cd['year'])})
        response += '\n'
    response += 'Thank you for using our service, to see other models that suits your requirements, visit our website.'

    return format_dialogflow_response([response])


def handle_user_denies_model(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    car_data = get_car_information(brand=brand)
    response = f'We have the following {brand} cars available:\n'
    for cd in car_data:
        response += get_response_from_responses_json(
            'do_not_car_data_whatsapp',
            {'{brand}': cd['brand'], '{model}': cd['model'], '{price}': str(cd['price']), '{year}': str(cd['year'])})
        response += '\n'
    response += 'Thank you for using our service, to see other models that suits your requirements, visit our website.'

    return format_dialogflow_response([response])
