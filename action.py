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


def call_fuzzy_wuzzy(reference_values: list[str], dialogflow_query: str = None, query_value: str = None) -> str | None:
    matched_value = None
    if query_value == None:
        match_percentage = 98.0
        for word in dialogflow_query.split(' '):
            processed = process.extractOne(word.upper(), reference_values)
            try:
                if processed[1] > match_percentage:
                    match_percentage = processed[1]
                    matched_value = str(processed[0])
                    return matched_value
            except:
                return None
    else:
        processed = process.extractOne(query_value.upper(), reference_values)
        try:
            matched_value = str(processed[0])
            return matched_value
        except:
            return matched_value


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
        brand = call_fuzzy_wuzzy(
            reference_values=brand_data, dialogflow_query=query)
    else:
        '''Dialogflow has extracted the car brand but still for sanity check
        matching it with the existing car brands
        '''
        brand_data = parameters['brand_data']
        brand = call_fuzzy_wuzzy(
            reference_values=brand_data, query_value=parameters['car_company'])
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
        model_data = get_model_information(brand)
        model = call_fuzzy_wuzzy(
            reference_values=model_data, dialogflow_query=query)
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
                'car_brand_found_model_not_found', {"{brand}": str(brand)})
        else:
            car_data = get_car_information(brand, model)
            if len(car_data) == 0:
                response = get_response_from_responses_json(
                    'car_model_found_no_car_db', {"{brand}": str(brand), "{model}": str(model)})
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
                    'car_model_found', {"{brand}": str(brand), "{model}": str(model), "{number}": str(len(car_data))})

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
        model = call_fuzzy_wuzzy(
            reference_values=model_data, dialogflow_query=query)
    else:
        '''Need to do a sanity check here, in case the model is not extracted, we need to say
        sorry, we don't have the model, we can suggest some cars
        '''
        model = call_fuzzy_wuzzy(
            reference_values=model_data, query_value=parameters['car_model'])
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
        if model == None:
            car_data = get_car_information(brand)
            if len(car_data) == 0:
                response = get_response_from_responses_json(
                    'car_found_no_model_found_no_car_db', {"{brand}": str(brand)})
            else:
                response = get_response_from_responses_json(
                    'car_found_user_denies_model', {"{brand}": str(brand), "{number}": str(len(car_data))})
        else:
            car_data = get_car_information(brand, model)
            if len(car_data) == 0:
                response = get_response_from_responses_json(
                    'car_model_found_no_car_db', {"{brand}": str(brand), "{model}": str(model)})
            else:
                response = get_response_from_responses_json(
                    'car_model_found', {"{brand}": str(brand), "{model}": str(model), "{number}": str(len(car_data))})
    else:
        if model == None:
            model = ''
        response = get_response_from_responses_json(
            'sell_car_model_found', {"{brand}": str(brand), "{model}": str(model)})

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
        order_number = parameters['order_number']
        more_information = ''
        response = get_response_from_responses_json(
            'order_number_found', {"{order_number}": str(order_number), "{more_information}": more_information})
    if flow == 'BUY':
        response = get_response_from_responses_json('send_car_data_whatsapp')
    elif flow == 'SELL':
        brand = parameters['brand']
        model = parameters['model']
        response = get_response_from_responses_json(
            'sell_send_car_data_whatsapp_or_no', {"{brand}": str(brand), "{model}": str(model)})
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
                    {'{brand}': str(cd['brand']), '{model}': str(cd['model']), '{price}': str(cd['price']), '{year}': str(cd['year'])})
                response += '\n'
            response += 'Thank you for using our service, to see other models that suits your requirements, visit our website.'
    elif flow == 'SELL':
        brand = parameters['brand']
        model = parameters['model']
        response = get_response_from_responses_json(
            'sell_send_car_data_whatsapp_or_no', {"{brand}": str(brand), "{model}": str(model)})
    else:
        response = get_response_from_responses_json(
            'order_send_or_not_whatsapp')

    return format_dialogflow_response(response)


def handle_user_denies_model(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    flow = parameters['flow']
    if flow == 'BUY':
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
            'car_found_user_denies_model', {"{brand}": str(brand), "{number}": str(len(car_data))})
    else:
        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-car-purchase-year',
                'lifespanCount': 1
            }
        )
        response = get_response_from_responses_json(
            'ask_manufacturing_year', {"{brand}": str(brand)})

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
        brand = call_fuzzy_wuzzy(
            reference_values=brand_data, dialogflow_query=query)
    else:
        '''Dialogflow has extracted the car brand but still for sanity check
        matching it with the existing car brands
        '''
        brand_data = parameters['brand_data']
        brand = call_fuzzy_wuzzy(
            reference_values=brand_data, query_value=parameters['car_company'])
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
        response = get_response_from_responses_json('sell_car_not_in_query')
    else:
        '''Car brand is found, making a wild guess to find the model from the query.
        '''
        model_data = get_model_information(brand)
        model = call_fuzzy_wuzzy(
            reference_values=model_data, dialogflow_query=query)
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
                'sell_car_found_model_not_found', {"{brand}": str(brand)})
        else:
            output_contexts = []
            output_contexts.append(
                {
                    'name': f'{session}/contexts/await-car-purchase-year',
                    'lifespanCount': 1
                }
            )
            response = get_response_from_responses_json(
                'ask_manufacturing_year', {"{brand}": str(brand)})

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


def handle_user_provides_brand(body: dict) -> dict:
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    flow = parameters['flow']
    if flow == 'BUY':
        return handle_buy_a_car(body)
    else:
        return handle_sell_a_car(body)


def handle_user_provides_purchase_year(body: dict) -> dict:
    session = str(body['session'])
    parameters = dict(get_dialogflow_parameters(body, 'session-vars'))
    brand = parameters['brand']
    model = parameters['model']
    year = parameters['year']
    output_contexts = []
    output_contexts.append(
        {
            'name': f'{session}/contexts/await-action',
            'lifespanCount': 1
        }
    )
    output_contexts.append(
        {
            'name': f'{session}/contexts/session-vars',
            'lifespanCount': 50,
            'parameters': {
                'brand': brand,
                'model': model,
                'year': year
            }
        }
    )
    response = get_response_from_responses_json(
        'sell_car_model_found', {"{brand}": str(brand), "{model}": str(model)})

    return format_dialogflow_response(response, output_contexts)
