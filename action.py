from utils import *
from database import *


def handle_use_openai(body: dict) -> dict:
    query = body['queryResult']['fulfillmentMessages'][0]['text']['text'][0]
    response = get_openai_response(f'''Please format the following sentence in a polite tone. \
SENTENCE: {query}''')

    return format_dialogflow_response([response])


def handle_buy_a_car(body: dict) -> dict:
    try:
        all_required_params_present = body['queryResult']['allRequiredParamsPresent']
    except:
        all_required_params_present = False

    session = body['session']

    if all_required_params_present:
        '''TODO
        [ ] get all the available options format it
        [ ] add them to the session parameters
        '''
        parameters = get_dialogflow_parameters(body, 'buy-session')

        brand = parameters['car_company']
        model = None
        fuel_type = None

        if parameters['car_model'] != '':
            model = parameters['car_model']
        if parameters['car_variant'] != '':
            fuel_type = parameters['car_variant']

        car_options = get_car_information(brand, model, fuel_type)

        if len(car_options) == 0:
            output_contexts = []
            response = get_openai_response(f'''Consider yourself as a car sales assistant, user is \
searching for card beand {brand} but unfortunately we don't have that in our listing, politely say \
that we don't have this car and Ask a follow up question to look for another car.''')
        else:
            response = get_openai_response(f'Consider yourself as a car sales assistant, format the \
following car options in a informative tone. Car options: {car_options} Ask a follow up question to \
select an option.')

            output_contexts = []
            output_contexts.append(
                {
                    'name': f'{session}/contexts/buy-session',
                    'lifespanCount': 50,
                    'parameters': {
                        'car_options': []
                    }
                }
            )
            output_contexts.append(
                {
                    'name': f'{session}/contexts/await-buy-option',
                    'lifespanCount': 1
                }
            )
    else:
        output_contexts = []
        response = get_openai_response(f'''Please format the following sentence in a polite tone. \
SENTENCE: {body['queryResult']['fulfillmentText']}''')

    return format_dialogflow_response([response], output_contexts)


def handle_user_provides_buy_option(body: dict) -> dict:
    session = body['session']
    parameters = get_dialogflow_parameters(body, 'buy-session')
    option = parameters['option']
    car_options = parameters['car_options']
    print(option)
    print(car_options)
    response = 'Good choice, before I provide you more information, I will ask you a few questions to get in touch with you. Is it okay with you?'
    output_contexts = []
    output_contexts.append(
        {
            'name': f'{session}/contexts/buy-session',
            'lifespanCount': 50,
            'parameters': {
                'next_yes_question': 'Please let me know your full name.',
                'next_yes_context': 'await-name',
                'next_no_question': 'Here is the more information about the car you selected.',
                'next_no_context': ''
            }
        }
    )
    output_contexts.append(
        {
            'name': f'{session}/contexts/await-action',
            'lifespanCount': 1
        }
    )

    return format_dialogflow_response([response], output_contexts)


def handle_confirm_action(body: dict) -> dict:
    session = body['session']
    parameters = get_dialogflow_parameters(body, 'session-vars')
    flow = parameters['flow']

    if flow == 'Buy':
        parameters = get_dialogflow_parameters(body, 'buy-session')
    else:
        parameters = get_dialogflow_parameters(body, 'sell-session')

    response = parameters['next_yes_question']
    context_name = parameters['next_yes_context']

    output_contexts = []

    if context_name == '':
        pass
    else:
        output_contexts.append(
            {
                'name': f'{session}/contexts/{context_name}',
                'lifespanCount': 1
            }
        )

    return format_dialogflow_response([response], output_contexts)


def handle_deny_action(body: dict) -> dict:
    session = body['session']
    parameters = get_dialogflow_parameters(body, 'session-vars')
    flow = parameters['flow']

    if flow == 'Buy':
        parameters = get_dialogflow_parameters(body, 'buy-session')
    else:
        parameters = get_dialogflow_parameters(body, 'sell-session')

    response = parameters['next_no_question']
    context_name = parameters['next_no_context']

    output_contexts = []

    if context_name == '':
        pass
    else:
        output_contexts.append(
            {
                'name': f'{session}/contexts/{context_name}',
                'lifespanCount': 1
            }
        )

    return format_dialogflow_response([response], output_contexts)


def handle_user_provides_name(body: dict) -> dict:
    session = body['session']
    parameters = get_dialogflow_parameters(body, 'session-vars')
    flow = parameters['flow']

    output_contexts = []

    '''TODO
    [ ] check if the mobile number is present in the request, based on that ask the next question
    '''

    if flow == 'Buy':
        parameters = get_dialogflow_parameters(body, 'buy-session')
        response = 'what is the best number to reach you?'
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-mobile',
                'lifespanCount': 1
            }
        )
    else:
        parameters = get_dialogflow_parameters(body, 'sell-session')
        response = 'what is the best number to reach you?'
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-mobile',
                'lifespanCount': 1
            }
        )

    return format_dialogflow_response([response], output_contexts)


def handle_user_provides_mobile(body: dict) -> dict:
    session = body['session']
    parameters = get_dialogflow_parameters(body, 'session-vars')
    flow = parameters['flow']

    output_contexts = []

    '''TODO
    [ ] add something in session to save the data
    '''

    if flow == 'Buy':
        response = 'Thank you, here are the more information about the car option you selected. \
Do you want to schedule a call.'

        option = parameters['option']
        car_options = parameters['car_options']
        print(option)
        print(car_options)

        output_contexts.append(
            {
                'name': f'{session}/contexts/buy-session',
                'lifespanCount': 50,
                'parameters': {
                    'next_yes_question': 'Thank you, someone from our team will give you a call on your number.',
                    'next_yes_context': '',
                    'next_no_question': 'Thank you for using our service, please let me know if you need anything.',
                    'next_no_context': ''
                }
            }
        )

        output_contexts.append(
            {
                'name': f'{session}/contexts/await-action',
                'lifespanCount': 1
            }
        )
    else:
        print('I am here...')
        parameters = get_dialogflow_parameters(body, 'sell-session')
        response = 'Thank you for these information, we will get in touch with you.'

    return format_dialogflow_response([response], output_contexts)


def handle_sell_a_car(body: dict) -> dict:
    try:
        all_required_params_present = body['queryResult']['allRequiredParamsPresent']
    except:
        all_required_params_present = False

    session = body['session']

    if all_required_params_present:
        '''TODO
        [ ] get all the available options format it
        [ ] add them to the session parameters
        '''
        parameters = get_dialogflow_parameters(body, 'sell-session')
        print(parameters)

        response = 'I have got all the information regarding your car. \
Would you like to provide your name and mobile number so that someone from \
our team will get in touch with you for the further process?'

        output_contexts = []
        output_contexts.append(
            {
                'name': f'{session}/contexts/sell-session',
                'lifespanCount': 50,
                'parameters': {
                    'next_yes_question': 'Please let me know your full name.',
                    'next_yes_context': 'await-name',
                    'next_no_question': 'Okay, is there anything I can help you with?',
                    'next_no_context': ''
                }
            }
        )
        output_contexts.append(
            {
                'name': f'{session}/contexts/await-action',
                'lifespanCount': 1
            }
        )
    else:
        output_contexts = []
        response = body['queryResult']['fulfillmentText']

    return format_dialogflow_response([response], output_contexts)
