import configparser
import google.generativeai as genai
from templates import function_creation_template, indent_template, save_plot_template

config = configparser.ConfigParser()
config.read(".config")

genai.configure(api_key=config["KEYS"]["API_KEY"])


def conclusion_agent(messages):

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="Put together all the messages and formulate a clear and short answer",
    )
    resp = client.generate_content(messages)

    return resp


def function_creation_agent(question, columns):

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a data analyst. Your task is to create functions and scripts to apply them to a dataframe to obtain results ",
    )
    resp = client.generate_content(
        function_creation_template.substitute(question=question, columns=columns),
    )

    return resp


def indent_agent(task, code):

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a programmer. Your task is to check if a code snippet answwers to a specific task. Correct ans reindent the code",
    )

    resp = client.generate_content(
        indent_template.substitute(task=task, code=code),
    )

    return resp


def save_plot_agent(script):

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a programmer. Your task is make changes to a script",
    )

    resp = client.generate_content(
        save_plot_template.substitute(script=script),
    )

    return resp


def check_api_key_agent(api_key):

    if api_key == "":
        return "empty_key"

    genai.configure(api_key=api_key)

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
    )

    try:
        resp = client.generate_content("Tell me a joke")
        return "valid_key"
    except Exception as e:
        if e.reason == "API_KEY_INVALID":
            return "invalid_key"
        else:
            return f"There was an error: {e}"
