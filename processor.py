import io
import sys
import json
import pandas as pd
import numpy as np
from typing import List
from contextlib import redirect_stdout
import plotly.express as px
import plotly.graph_objects as go
from agents import function_creation_agent, indent_agent
from functions import print_colored, read_table

# create data
dff = read_table(sys.argv[1])
columns = dff.columns.to_list()


def process_question(
    question: str, columns: List[str], diagnostic: bool = True
) -> str | None:
    """Send to LLM the question about the data frame.
    Receive a snippet of code in string format or None if the question is not about the data frame.

    Args:
        question (str): question or a task about the dataframe
        columns (List[str]): the column names
        diagnostic (bool, optional): use print statements to display intermediate responses. Defaults to True.

    Returns:
        str: snippet of code
    """

    # generate the first response. None if the question does not refer to data frame
    raw_response = function_creation_agent(question, columns)

    # extract the generated code from JSON
    code_response = json.loads(raw_response.text, strict=False)["answer"]

    print_colored("\nCODE RESPONSE:\n" + code_response, color="green")

    # false is returned when the question is not about tah data frame
    if code_response == "false":
        return
    else:

        # reindent the code an optimize it
        raw_response = indent_agent(task=question, code=code_response)

        # extract the code
        indent_response = json.loads(raw_response.text, strict=False)["answer"]

        print_colored("\nCODE OPTIMIZATION\n" + indent_response, color="green")

        return indent_response


def cycle_message() -> None:
    """Create a cycle where the user asks a question and the program responds."""

    try:
        while True:

            # if the column names changes, update in template
            columns = dff.columns.to_list()

            question = input("\n\nAsk a question about the data:\n")

            # empty questions are not accepted
            if question == "" or question is None:
                continue

            # call the function to receive the code
            indent_response = process_question(question, columns)

            # empty response will make the program ask again
            if indent_response is None:
                continue
            else:

                try:
                    # initialize a string to capture the response from print statement
                    output_capture = io.StringIO()

                    # capture response
                    with redirect_stdout(output_capture):
                        # execute the generated code
                        exec(indent_response)

                    # print the response. if a plot is generated, then a browser will be opened to display it
                    captured_output = output_capture.getvalue()
                    print("Captured Output:\n", captured_output)

                # any exception is printed and the user can ask another question
                except Exception as e:
                    print(e)

    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    cycle_message()


if __name__ == "__main__":
    main()
