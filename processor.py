import sys
import json
import configparser
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from functions import read_table
from reason_agents import DfOaCodeAgent

config = configparser.ConfigParser()
config.read(".config")


def cycle_message(dff) -> None:
    """Create a cycle where the user asks a question and the program responds."""

    cda = DfOaCodeAgent(dff, api_key=config["KEYS"]["O_API_KEY"])

    try:
        while True:

            question = input("\n\nAsk a question about the data:\n")

            # empty questions are not accepted
            if question == "" or question is None:
                continue

            resp = cda.generate_content(question)

            if resp.get("code_run"):
                if resp["code_run"].get("output"):
                    print(resp["code_run"]["output"])
                else:
                    print(resp["code_run"]["exception"])
            else:
                print(
                    json.loads(resp["model"].choices[0].message.content, strict=False)[
                        "explanation"
                    ]
                )

    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    # create data
    dff = read_table(sys.argv[1])
    cycle_message(dff)


if __name__ == "__main__":
    main()
