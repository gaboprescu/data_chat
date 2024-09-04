import io
import re
import json
import pandas as pd
import numpy as np
from contextlib import redirect_stdout
import plotly.express as px
import plotly.graph_objects as go
from agents import function_creation_agent, conclusion_agent, indent_agent
from functions import clean_dict, print_colored

# create data
data = pd.read_csv("./data/student-perf.csv", sep=",")
dff = pd.DataFrame(data)
columns = dff.columns.to_list


def execute_code(code):
    exec(code)
    # loc_dict = locals()
    # return loc_dict


def process_question(question):

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

            # agent_message = []

            question = input("\n\nAsk a question about the data:\n")

            if question == "" or question is None:
                continue

            indent_response = process_question(question)

            # raw_response = function_creation_agent(question, columns)

            # code_response = json.loads(raw_response.text, strict=False)["answer"]

            # print_colored("\nCODE RESPONSE:\n" + code_response, color="green")

            # if code_response == "false":
            if indent_response is None:
                continue
            else:

                # raw_response = indent_agent(task=question, code=code_response)

                # indent_response = json.loads(raw_response.text, strict=False)["answer"]

                # print_colored("\nCODE OPTIMIZATION\n" + indent_response, color="green")

                # agent_message.append({"role": "user", "content": question})
                # agent_message.append({"role": "assistant", "content": indent_response})

                try:
                    output_capture = io.StringIO()

                    with redirect_stdout(output_capture):
                        execute_code(indent_response)

                    captured_output = output_capture.getvalue()
                    print("Captured Output:\n", captured_output)
                    # lc_dict = execute_code(indent_response)
                    #! introduce prea multe date. lasa doar codul
                    # lc_dict = clean_dict(lc_dict)

                    # agent_message.append(
                    #     {"role": "user", "content": str(lc_dict)}
                    # )  # l-am lasat
                except Exception as e:
                    print(e)
                    # agent_message.append({"role": "user", "content": str(e)})

            # if (
            #     re.search("plot|figure|plotly", agent_message[-1]["content"])
            #     is not None
            # ):
            #     pass
            # else:
            #     pass
            # pprint(agent_message)
            # conc = conclusion_agent(agent_message)
            # print("\n" + conc.choices[0].message.content)

    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    cycle_message()


if __name__ == "__main__":
    main()
