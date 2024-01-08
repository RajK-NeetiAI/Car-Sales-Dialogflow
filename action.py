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

    return format_dialogflow_response(response, output_contexts)


def handle_buy_a_car(body: dict) -> dict:
    query = str(body['queryResult']['queryText'])
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    if 'brand_data' not in parameters.keys():
        brand_data = get_brand_information()
        parameters.update({'brand_data': brand_data})
    brand = None
    model = None
    if parameters['car_company'] == '':
        '''When car is not extracted from the Dialogflow
        Try to match it using fuzzywuzzy
        '''
        brand_data = parameters['brand_data']
        match_percentage = 95.0
        for word in query.split(' '):
            processed = process.extractOne(word.upper(), brand_data)
            if processed[1] > match_percentage:
                match_percentage = processed[1]
                brand = str(processed[0])
    else:
        '''Dialogflow has extracted the car brand but still for sanity check
        matching it with the existing car brands
        '''
        brand_data = parameters['brand_data']
        processed = process.extractOne(
            parameters['car_company'].upper(), brand_data)
        brand = str(processed[0])

    if brand == None:
        '''If user has just queried without car brand and model name,
        ask either they are looking for a specific brand
        '''
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-car-brand',
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
        response = get_response_from_responses_json('car_not_in_query')
    else:
        '''Car brand is found, making a wild guess to find the model from the query.
        '''
        match_percentage = 95.0
        model_data = get_model_information(brand)
        for word in query.split(' '):
            processed = process.extractOne(word.upper(), model_data)
            if processed[1] > match_percentage:
                match_percentage = processed[1]
                model = str(processed[0])
        if model == None:
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
                        'brand': brand,
                        'model_data': model_data,
                        'model': model
                    }
                }
            )
            response = get_response_from_responses_json(
                'car_brand_found_model_not_found', {"{brand}": brand})
        else:
            car_data = get_car_information(brand, model)
            output_contexts = []
            output_contexts.append(
                {
                    'name': f'{session}/contexts/session-vars',
                    'lifespanCount': 50,
                    'parameters': {
                        'brand_data': brand_data,
                        'brand': brand,
                        'model_data': model_data,
                        'model': model
                    }
                }
            )
            response = get_response_from_responses_json(
                'car_model_found', {"{brand}": brand, "{model}": model, "{number}": len(car_data)})

    return format_dialogflow_response(response, output_contexts)


def handle_user_provides_model(body: dict) -> dict:
    query = str(body['queryResult']['queryText'])
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    flow = parameters['flow']
    model_data = get_model_information(brand)
    model = None
    if parameters['car_model'] == '':
        '''Model not found through Dialogfloe, trying to extract it from existing models
        '''
        match_percentage = 95.0
        model_data = get_model_information(brand)
        for word in query.split(' '):
            processed = process.extractOne(word.upper(), model_data)
            if processed[1] > match_percentage:
                match_percentage = processed[1]
                model = str(processed[0])
    processed = process.extractOne(parameters['car_model'], model_data)
    '''Need to do a sanity check here, in case the model is not extracted, we need to say
    sorry, we don't have the model, we can suggest some cars
    '''
    try:
        model = str(str(processed[0]))
    except:
        pass
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
    if flow == 'BUY':
        response = get_response_from_responses_json(
            'car_model_found', {"{brand}": brand, "{model}": model})
    else:
        if model == None:
            model = ''
        response = get_response_from_responses_json(
            'sell_car_model_found', {"{brand}": brand, "{model}": model})

    return format_dialogflow_response(response, output_contexts)


def handle_user_confirms_details_over_whatsapp(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    flow = parameters['flow']
    '''User mobile number
    '''
    print(body['originalDetectIntentRequest']['payload'])
    '''User wants to receive the details over WhatsApp
    '''
    if flow == 'BUY':
        '''TODO
        [ ] format the car data
        [ ] send the car data to the WhatsApp
        [ ] make sure the car data is not empty
        '''
        brand = parameters['brand']
        model = parameters['model']
        car_data = get_car_information(brand, model)
        print(car_data)
    if flow == 'ORDER':
        '''TODO
        [ ] get the order number from the request
        [ ] make an API call to fetch the order status from backend
        [ ] send the data to WhatsApp
        '''
        order_number = 12345
        more_information = ''
        response = get_response_from_responses_json(
            'order_number_found', {"{order_number}": str(order_number), "{more_information}": more_information})
    if flow == 'BUY':
        response = get_response_from_responses_json('send_car_data_whatsapp')
    elif flow == 'SELL':
        response = get_response_from_responses_json(
            'sell_send_car_data_whatsapp_or_no', {"{brand}": brand, "{model}": model})
    else:
        response = get_response_from_responses_json(
            'order_send_or_not_whatsapp')

    return format_dialogflow_response(response)


def handle_user_denies_details_over_whatsapp(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    flow = parameters['flow']
    if flow == 'BUY':
        brand = parameters['brand']
        model = parameters['model']
        car_data = get_car_information(brand=brand, model=model)
        if len(car_data) == 0:
            response = get_response_from_responses_json('car_data_empty')
        else:
            response = f'We have the following {brand} {model} cars available:\n'
            for cd in car_data:
                response += get_response_from_responses_json(
                    'do_not_car_data_whatsapp',
                    {'{brand}': cd['brand'], '{model}': cd['model'], '{price}': str(cd['price']), '{year}': str(cd['year'])})
                response += '\n'
            response += 'Thank you for using our service, to see other models that suits your requirements, visit our website.'
    elif flow == 'SELL':
        response = get_response_from_responses_json(
            'sell_send_car_data_whatsapp_or_no', {"{brand}": brand, "{model}": model})
    else:
        response = get_response_from_responses_json(
            'order_send_or_not_whatsapp')

    return format_dialogflow_response(response)


def handle_user_denies_model(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    car_data = get_car_information(brand=brand)
    output_contexts = []
    output_contexts.append(
        {
            'name': f'{session}/contexts/session-vars',
            'lifespanCount': 50,
            'parameters': {
                'model_data': [],
                'model': None,
                'car_data': car_data
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
        'car_found_user_denies_model', {"{brand}": brand, "{number}": len(car_data)})

    return format_dialogflow_response(response, output_contexts)


def handle_sell_a_car(body: dict) -> dict:
    query = str(body['queryResult']['queryText'])
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    if 'brand_data' not in parameters.keys():
        brand_data = get_brand_information()
        parameters.update({'brand_data': brand_data})
    brand = None
    model = None
    if parameters['car_company'] == '':
        '''When car is not extracted from the Dialogflow
        Try to match it using fuzzywuzzy
        '''
        brand_data = parameters['brand_data']
        match_percentage = 95.0
        for word in query.split(' '):
            processed = process.extractOne(word.upper(), brand_data)
            if processed[1] > match_percentage:
                match_percentage = processed[1]
                brand = str(processed[0])
    else:
        '''Dialogflow has extracted the car brand but still for sanity check
        matching it with the existing car brands
        '''
        brand_data = parameters['brand_data']
        processed = process.extractOne(
            parameters['car_company'].upper(), brand_data)
        brand = str(processed[0])

    if brand == None:
        '''If user has just queried without car brand and model name,
        ask either they are looking for a specific brand
        '''
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-car-brand-sell',
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
        response = get_response_from_responses_json('sell_car_not_in_query')
    else:
        '''Car brand is found, making a wild guess to find the model from the query.
        '''
        match_percentage = 95.0
        model_data = get_model_information(brand)
        for word in query.split(' '):
            processed = process.extractOne(word.upper(), model_data)
            if processed[1] > match_percentage:
                match_percentage = processed[1]
                model = str(processed[0])
        if model == None:
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
                        'brand': brand,
                        'model_data': model_data,
                        'model': model
                    }
                }
            )
            response = get_response_from_responses_json(
                'sell_car_found_model_not_found', {"{brand}": brand})
        else:
            output_contexts = []
            output_contexts.append(
                {
                    'name': f'{session}/contexts/session-vars',
                    'lifespanCount': 50,
                    'parameters': {
                        'brand_data': brand_data,
                        'brand': brand,
                        'model_data': model_data,
                        'model': model
                    }
                }
            )
            response = get_response_from_responses_json(
                'sell_car_model_found', {"{brand}": brand, "{model}": model})

    return format_dialogflow_response(response, output_contexts)


def handle_order_status(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    order_number = parameters['order_number']
    if order_number == '':
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-order-number',
                'lifespanCount': 1
            }
        )
        response = get_response_from_responses_json('order_number_not_found')
    else:
        '''TODO
        [ ] make an API call to fetch the order status from backend
        '''
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-action',
                'lifespanCount': 1
            }
        )
        more_information = ''
        response = get_response_from_responses_json(
            'order_number_found', {"{order_number}": str(order_number), "{more_information}": more_information})

    return format_dialogflow_response(response, output_contexts)


def handle_user_provides_order_number(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    order_number = parameters['order_number']
    if order_number == '':
        output_contexts = []
        response = get_response_from_responses_json('order_number_not_known')
    else:
        '''TODO
        [ ] make an API call to fetch the order status from backend
        '''
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-action',
                'lifespanCount': 1
            }
        )
        more_information = ''
        response = get_response_from_responses_json(
            'order_number_found', {"{order_number}": str(order_number), "{more_information}": more_information})

    return format_dialogflow_response(response, output_contexts)
