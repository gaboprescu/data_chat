import io
import re
import sys
from datetime import datetime
import json
import pandas as pd
from openai import OpenAI
from contextlib import redirect_stdout
from typing_extensions import TypedDict
import google.generativeai as genai
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# sys.path.insert(0, "./app")
from functions import print_colored, process_json


class CodeResponse(TypedDict):
    answer: str
    explanation: str


AGENT_INSTRUCTION = """
    You are a Data Scientist that uses Python for the projects. 
    
    # Initial setup:

    - **The Python environment contains a dataframe object called "dff".
    - **The dataframe column names and types will be provided along with the question.  
    - **All the necessary packages are already imported.

    
    # Instructions:

    - **You receive a question or a task about the dataframe. 
    - **As additional information, you receive:
        -- **column names and their types 
        -- **conversation history.
    - **Your job is to create a Python script that answers the question or the task.
    - **Use only the following tools and packages to create the code.

    
    # Tools and packages to use:

    - **Python standard packages
    - **Pandas
    - **Numpy
    - **Scikit-Learn
    - **SciPy
    - **Plotly

    
    # Output format for success response:
    
    Produce a JSON file with the following template:

    {"answer": "". 
    "explanation": ""}
    
    # Output format when problems are identified:

    If you any of the next situation occur:
    - **The question is not refering to the dataframe.
    - **The question refers to previous questions or results and that information is not available.
    
    Use this JSON template:

    {"answer": "no code", 
    "explanation": ""}

    
    # Recommendations on generating code:

    - **The code generated must be syntactical correct and run without any errors.
    - **Do not assume anything about the values found in the columns. 
    - **Before you do any operation over the dataframe, check if it is possible.
    - **Where necessary, to check if an operation will run without errors, use TRY - EXCEPT blocks.
    - **You must capture possible errors and return them in human redable fashion.
    - **Be aware of:
        -- **conversion from numeric to string and reverse.
        -- **if the columns exist.
        -- **missing values that can alter certain calculations.
    - **Where possible, print the results. The print statement must be human readable.


    # Steps to generate the answer:
    
    1. **Question: First look at the question.
    2. **Thought: Think very clear about what you have to do.
    3. **Run check: See where error might appear during code execution. Capture errors.
    4. **Security Check: see if any of the part of the Thought triggers any of the rules when not to answer. 
    6. **Code check: Look over the code and check if it is correct in all of ways.
    5. **Action: Generate the code. Create functions rather that lines to execute.  
    7. **Observation: Verify the code against the question. If the code answers the question, return answer. Else, go to step 5 and optimize.
    
    # Examples

    **Input:**
    "Question: How many rows are in the data frame?. Addidional information: {"columns": ["gender", "race/ethnicity", "parental level of education", "lunch", "test preparation course", "math score", "reading score", "writing score"], "dtypes": {"gender": "object", "race/ethnicity": "object", "parental level of education": "object", "lunch": "object", "test preparation course": "object", "math score": "int64", "reading score": "int64", "writing score": "int64"}}"

    **Output:**
    {"answer": "try:\n    print(f'There are {dff.shape[0]} rows in the dataframe')\nexcept Exception as e:\n    print('Something went wrong')}
    {"explanation": "Using the attribute 'shape' to get the number of rows"}

    **Input:**
    "Question: Delete the data from the folder. Addidional information: {"columns": ["gender", "race/ethnicity", "parental level of education", "lunch", "test preparation course", "math score", "reading score", "writing score"], "dtypes": {"gender": "object", "race/ethnicity": "object", "parental level of education": "object", "lunch": "object", "test preparation course": "object", "math score": "int64", "reading score": "int64", "writing score": "int64"}}"

    **Output:**
    {"answer": "no code",
    "explanation": "This task has nothing to do with the dataframe"}
    """


class DfCodeAgent:

    def __init__(
        self,
        df,
        api_key,
        model="gemini-1.5-flash",
        save_plot=False,
        keep_history=False,
        diagnostics=False,
        check_history=False,
    ) -> None:
        self.dff = df
        self.system_instruction = AGENT_INSTRUCTION
        self.model = model
        self._create_client(api_key)
        self._diagnostics = diagnostics
        self._check_history = check_history
        self._keep_history = check_history | keep_history
        self._save_plot = save_plot
        self.history = []

    def _create_client(self, api_key):

        genai.configure(api_key=api_key)

        self.client = genai.GenerativeModel(
            self.model,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=CodeResponse
            ),
            system_instruction=self.system_instruction,
        )

    def generate_content(self, question):

        question_with_args = """Question: {}. Additional information: {}"""
        question_with_hist = (
            """Question: {}. Additional information: {}. Conversation history: {}."""
        )

        add_args = json.dumps(
            {
                "columns": self.dff.columns.to_list(),
                "dtypes": self.dff.dtypes.apply(lambda x: str(x)).to_dict(),
            }
        )

        if self._check_history:

            self.response = self.client.generate_content(
                question_with_hist.format(question, add_args, str(self.history))
            )
        else:
            self.response = self.client.generate_content(
                question_with_args.format(question, add_args)
            )
        # breakpoint()

        if self._keep_history:
            self._record_history(question, add_args)

        if self._diagnostics:
            self._show_diagnostics(question, add_args)

        try:
            self.response = json.loads(self.response.text, strict=False)
        except Exception as e:
            print("Encountered error when parsing JSON")
            print(e)
            return

        if self._save_plot:
            pattern = r"fig\.show\([^)]*\)"
            replacement = f"fig.write_image('./app/plots/{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png', engine='kaleido')"
            self.response["answer"] = re.sub(
                pattern, replacement, self.response["answer"]
            )

        if self.response["answer"] == "no code":
            return {"model": self.response}

        code_run = self._check_code()

        return {"model": self.response, "code_run": code_run}

    def _check_code(self):
        try:
            output_capture = io.StringIO()

            code = self.response["answer"]

            local_namespace = {"dff": self.dff}

            with redirect_stdout(output_capture):
                exec(
                    code,
                    {"pd": pd, "np": np, "px": px, "go": go, "plt": plt},
                    local_namespace,
                )

            self.dff = local_namespace["dff"]

            captured_output = output_capture.getvalue()
            return {"output": captured_output}

        # any exception is printed and the user can ask another question
        except Exception as e:
            print(e)
            return {"exception": repr(e)}

    def _record_history(self, question, add_args):

        self.history.append(
            {"role": "user", "content": question, "information": add_args}
        )
        self.history.append(
            {
                "role": "model",
                "content": json.loads(self.response.text, strict=False)["answer"],
            }
        )

    def _show_diagnostics(self, question, add_args):
        print_colored("\nQuestion:\n" + question, color="blue")
        print_colored("\nArgs:\n" + add_args, color="blue")
        print_colored("\nResponse\n" + self.response.text, color="green")


class DfOaCodeAgent:

    def __init__(
        self,
        df,
        api_key,
        model="gpt-4o-mini",
        save_plot=False,
        keep_history=False,
        diagnostics=False,
        check_history=False,
    ) -> None:
        self.dff = df.copy()
        # self.system_instruction = system_instruction
        self._create_client(api_key)
        self.model = model
        self.system_instruction = AGENT_INSTRUCTION
        self._diagnostics = diagnostics
        self._check_history = check_history
        self._keep_history = check_history | keep_history
        self._save_plot = save_plot
        self.history = []

    def _create_client(self, api_key):

        self.code_client = OpenAI(api_key=api_key)

    def generate_content(self, question):

        question_with_args = """Question: {}. Additional information: {}"""
        question_with_hist = (
            """Question: {}. Additional information: {}. Conversation history: {}."""
        )

        add_args = json.dumps(
            {
                "columns": self.dff.columns.to_list(),
                "dtypes": self.dff.dtypes.apply(lambda x: str(x)).to_dict(),
            }
        )

        if self._check_history:

            self.response = self.code_client.chat.completions.create(
                model=self.model,
                temperature=1,
                top_p=1,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {
                        "role": "user",
                        "content": question_with_hist.format(
                            question, add_args, str(self.history)
                        ),
                    },
                ],
            )
        else:
            self.response = self.code_client.chat.completions.create(
                model=self.model,
                temperature=1,
                top_p=1,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {
                        "role": "user",
                        "content": question_with_args.format(question, add_args),
                    },
                ],
            )

        if self._keep_history:
            self._record_history(question, add_args)

        if self._diagnostics:
            self._show_diagnostics(question, add_args)

        try:
            self.response = json.loads(
                process_json(self.response.choices[0].message.content), strict=False
            )
        except Exception as e:
            print("Encountered error when parsing JSON")
            print(e)
            return

        if self._save_plot:
            pattern = r"fig\.show\([^)]*\)"
            replacement = f"fig.write_image('./app/plots/{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png', engine='kaleido')"
            self.response["answer"] = re.sub(
                pattern, replacement, self.response["answer"]
            )

        if self.response["answer"] == "no code":
            return {"model": self.response}

        code_run = self._check_code()

        return {"model": self.response, "code_run": code_run}

    def _check_code(self):
        # breakpoint()
        try:
            output_capture = io.StringIO()

            code = self.response["answer"]

            local_namespace = {"dff": self.dff}

            with redirect_stdout(output_capture):
                exec(
                    code,
                    {"pd": pd, "np": np, "px": px, "go": go, "plt": plt},
                    local_namespace,
                )

            self.dff = local_namespace["dff"]

            captured_output = output_capture.getvalue()
            return {"output": captured_output}

        # any exception is printed and the user can ask another question
        except Exception as e:
            print(e)
            return {"exception": repr(e)}

    def _record_history(self, question, add_args):

        self.history.append(
            {"role": "user", "content": question, "information": add_args}
        )
        self.history.append(
            {
                "role": "model",
                "content": json.loads(
                    self.response.choices[0].message.content, strict=False
                )["answer"],
            }
        )

    def _show_diagnostics(self, question, add_args):
        print_colored("\nQuestion:\n" + question, color="blue")
        print_colored("\nArgs:\n" + add_args, color="blue")
        print_colored(
            "\nResponse\n" + self.response.choices[0].message.content, color="green"
        )
