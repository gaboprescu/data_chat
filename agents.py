import configparser
from typing import List, Dict, Union
from openai import OpenAI
import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse
from templates import function_creation_template, indent_template, save_plot_template

config = configparser.ConfigParser()
config.read(".config")

genai.configure(api_key=config["KEYS"]["G_API_KEY"])


def conclusion_agent(messages: List[Dict]) -> GenerateContentResponse:
    """Agent that takes the question, the generated code and the code execution results and formulates a response.

    Args:
        messages (_type_): List of dicts where the responses are recorded with the right role.

    Returns:
        _type_: the LLM response
    """

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="Put together all the messages and formulate a clear and short answer",
    )
    resp = client.generate_content(messages)

    return resp


def function_creation_agent(
    question: str, columns: List[str]
) -> GenerateContentResponse:
    """Agent to create code based on the question and column names.

    Args:
        question (str): question about the data frame
        columns (List[str]): the column names of the data frame

    Returns:
        GenerateContentResponse: LLM response
    """

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a data analyst. Your task is to create functions and scripts to apply them to a dataframe to obtain results ",
    )
    resp = client.generate_content(
        function_creation_template.substitute(question=question, columns=columns),
    )

    return resp


def indent_agent(task: str, code: str) -> GenerateContentResponse:
    """Agent to reindent and optimize the code relative to the task.

    Args:
        task (str): question or task used to generate the code
        code (str): the code generated

    Returns:
        GenerateContentResponse: response of the LLM
    """

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a programmer. Your task is to check if a code snippet answwers to a specific task. Correct ans reindent the code",
    )

    resp = client.generate_content(
        indent_template.substitute(task=task, code=code),
    )

    return resp


def save_plot_agent(script: str) -> GenerateContentResponse:
    """Agent to make changes to a script if the script generates a plot.
    The aim is to change the act of displaying the plot, into saving the plot locally.
    If the script does not generate a plot, the code is returned withput changes

    Args:
        script (str): snippet of code

    Returns:
        GenerateContentResponse: LLM response
    """

    client = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
        system_instruction="You are a programmer. Your task is make changes to a script",
    )

    resp = client.generate_content(
        save_plot_template.substitute(script=script),
    )

    return resp
