import io
import re
import json
import pandas as pd
import numpy as np
from contextlib import redirect_stdout
import plotly.express as px
import plotly.graph_objects as go
from agents import function_creation_agent, indent_agent
from functions import print_colored

# create data
data = pd.read_csv("./data/student-perf.csv", sep=",")
dff = pd.DataFrame(data)
columns = dff.columns.to_list


def process_question(question, columns):

    raw_response = function_creation_agent(question, columns)

    code_response = json.loads(raw_response.text, strict=False)["answer"]

    print_colored("\nCODE RESPONSE:\n" + code_response, color="green")

    if code_response == "false":
        return
    else:

        raw_response = indent_agent(task=question, code=code_response)

        indent_response = json.loads(raw_response.text, strict=False)["answer"]

        print_colored("\nCODE OPTIMIZATION\n" + indent_response, color="green")

        return indent_response


def cycle_message():

    try:
        while True:

            question = input("\n\nAsk a question about the data:\n")

            if question == "" or question is None:
                continue

            indent_response = process_question(question)

            if indent_response is None:
                continue
            else:

                try:
                    output_capture = io.StringIO()

                    with redirect_stdout(output_capture):
                        exec(indent_response)

                    captured_output = output_capture.getvalue()
                    print("Captured Output:\n", captured_output)

                except Exception as e:
                    print(e)

    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    cycle_message()


if __name__ == "__main__":
    main()
