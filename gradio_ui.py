import os
import json

from tenacity import retry, wait_random_exponential, stop_after_attempt
import requests
import gradio as gr
from dotenv import load_dotenv, find_dotenv

from database import get_car_information

load_dotenv(find_dotenv())


GPT_MODEL = "gpt-3.5-turbo-0613"


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_car_buying_information",
            "description": "Collect information about a car to buy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "The name of the car brand, e.g. Honda",
                    },
                    "model": {
                        "type": "string",
                        "description": "The name of the car model, e.g. Jazz",
                    },
                    "fuel_type": {
                        "type": "string",
                        "enum": ["Diesel", "Petrol", 'Gas'],
                        "description": "The fuel type of the car, e.g. Diesel",
                    }
                },
                "required": ["brand", "model", "fuel_type"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_car_selling_information",
            "description": "Collect information about a car to sell.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "The name of the car brand, e.g. Honda",
                    },
                    "model": {
                        "type": "string",
                        "description": "The name of the car model, e.g. Jazz",
                    },
                    "fuel_type": {
                        "type": "string",
                        "enum": ["Diesel", "Petrol", 'Gas'],
                        "description": "The fuel type of the car, e.g. Diesel",
                    },
                    "purchase_year": {
                        "type": "integer",
                        "description": "The purchase year of the car, e.g. 2012",
                    }
                },
                "required": ["brand", "model", "fuel_type", "purchase_year"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_information",
            "description": "Get the user name and mobile number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the user e.g. Rajesh",
                    },
                    "mobile": {
                        "type": "integer",
                        "description": "The mobile number of the user e.g. 9999999999",
                    }
                },
                "required": ["name", "mobile"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_car_option",
            "description": "Get the option of car selected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "option": {
                        "type": "integer",
                        "description": "The option selection from the list e.g. 1",
                    }
                },
                "required": ["option"],
            },
        }
    }
]


def format_chat_history(query: str, chat_history: list[list] = None) -> list[list]:
    formatted_chat_history = []
    if chat_history != None:
        for ch in chat_history:
            formatted_chat_history.append({"role": "user", "content": ch[0]})
            formatted_chat_history.append({"role": "system", "content": ch[1]})
    formatted_chat_history.append({"role": "user", "content": query})
    return formatted_chat_history


def handle_get_car_buying_information(function: dict[str, str]) -> str:
    parameters = json.loads(function['arguments'])
    brand = parameters['brand']
    model = parameters['model']
    fuel_type = parameters['fuel_type']
    car_information = get_car_information(
        brand=brand,
        model=model,
        fuel_type=fuel_type
    )
    if len(car_information) == 0:
        formatted_chat_history = format_chat_history(f'''Please rephrase the information \
in very polite way about a car of a brand {brand}, model {model}, and fuel type {fuel_type}, \
it is not in the car listings. Ask a follow up question if the user is looking for another \
car options.''')
        chat_response = chat_completion_request(formatted_chat_history)
        assistant_response = chat_response.json()["choices"][0]["message"]
        content = assistant_response['content']

        return content
    else:
        formatted_chat_history = format_chat_history(f'''User has inquired about a car of a \
brand {brand}, model {model}, and fuel type {fuel_type}. \
Here is the found car listing in JSON format: {car_information}. \
Please rephrase this in an informatiove tone and ask user about which one they liked.''')
        chat_response = chat_completion_request(
            formatted_chat_history, tools=tools)
        assistant_response = chat_response.json()["choices"][0]["message"]
        content = assistant_response['content']

        return content


def handle_conversation(chat_history: list[list]) -> list[list]:
    query = chat_history[-1][0]
    formatted_chat_history = format_chat_history(query, chat_history[:-1])
    chat_response = chat_completion_request(
        formatted_chat_history, tools=tools
    )
    assistant_response = chat_response.json()["choices"][0]["message"]
    if assistant_response['content'] == None:
        function = assistant_response['tool_calls'][0]['function']
        if function['name'] == 'get_car_buying_information':
            content = handle_get_car_buying_information(function)
        elif function['name'] == 'get_user_information':
            '''[ ] save the buyer infromation
            '''
            content = f'Thank you for this inqury, someone from our team will reach to you.'
        elif function['name'] == 'get_car_option':
            formatted_chat_history = format_chat_history(f'''''')
        chat_response = chat_completion_request(
            formatted_chat_history, tools=tools)
        assistant_response = chat_response.json()["choices"][0]["message"]
        content = assistant_response['content']
    else:
        content = assistant_response['content']
    chat_history[-1][1] = content

    return chat_history


def handle_user_query(message: str, chat_history: list[tuple]) -> tuple:
    chat_history += [[message, None]]
    return '', chat_history


with gr.Blocks(
    css='footer {visibility: hidden}'
) as demo:
    chatbot = gr.Chatbot(label='Talk to the Douments', bubble_full_width=False)
    msg = gr.Textbox(label='Query', placeholder='Enter text and press enter')
    clear = gr.ClearButton([msg, chatbot], variant='stop')
    msg.submit(
        handle_user_query,
        [msg, chatbot],
        [msg, chatbot]
    ).then(
        handle_conversation,
        [chatbot],
        [chatbot]
    )

demo.queue()
