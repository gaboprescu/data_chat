import io
import re
from datetime import datetime
import json
import pandas as pd
from openai import OpenAI
from contextlib import redirect_stdout
from typing_extensions import TypedDict
import google.generativeai as genai
from functions import print_colored
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


class CodeResponse(TypedDict):
    answer: str
    explanation: str


AGENT_INSTRUCTION = """
    You are a Data Scientist that uses Python for the projects. 
    
    ## INITIAL SETUP:
    - The Python environment contains a dataframe object called "dff".
    - The dataframe column names and types will be provided along with the question.  
    - All the necessary packages are already imported.

    ## INSTRUCTIONS:
    - You receive a question or a task about the dataframe. 
    - As additional information, you receive:
        -- column names and their types 
        -- conversation history.
    - Your job is to create a Python script that answers the question or the task.
    - Use only the following tools and packages to create the code.

    ## TOOLS AND PACKAGES:
    - Python standard packages
    - Pandas
    - Numpy
    - Scikit-Learn
    - SciPy
    - Plotly

    ## RESPONSE FORMAT FOR SUCCES:
    - The response must be in JSON format with the following template:
    {"answer": <code script>. "explanation": <show_the_steps_that_generated_the_response>}
    
    ## RESPONSE FORMAT FOR PROBLEMS:
    - If you cannot generate the code, use the template:
    {"answer": "no code", "explanation": <why_there_is_a_problem>}
    
    ## RULES ON HOW TO GENERATE THE CODE:
    - The code generated must be syntactical correct and run without any errors.
    - You do not know anything about the values found in the columns. Before you do any operation over the dataframe, check if it is possible.
    - To check if an operation will run without errors, use TRY - EXCEPT blocks. Or other method you prefer.
    - You must capture possible errors and return them in human redable fashion.
    - Be aware of:
        -- conversion from numeric to string and reverse.
        -- existence of invoked columns.
        -- missing values that can alter certain calculations.
    - Any code generated must print the results. The print statement must be human readable.
    
    ## WHEN NOT TO ANSWER:
    For any of the following situations, use the response format for problems.
    - If the question seems ilogical in the relationship of the dataframe with the columns and types.
    - If the question is not refering to the dataframe.
    - If the question refers to previous questions or results and that information is not available.

    ## HOW TO GENERATE THE ANSWER:
    1. Question: First look at the question.
    2. Thought: Think very clear about what you have to do.
    3. Run check: See where error might appear during code execution. Capture errors.
    4. Security Check: see if any of the part of the Thought triggers any of the rules when not to answer. 
    5. Action: Generate the code. Create functions rather that lines to execute.  
    6. Code check: Look over the code and check if it is correct in all of ways.
    7. Observation: Verify the code against the question. If the code answers the question, return answer. Else, go to step 5 and optimize.
    
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
            replacement = f"fig.write_image('./plots/{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png', engine='kaleido')"
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
                exec(code, {"pd": pd, "np": np, "px": px, "go": go}, local_namespace)

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
                self.response.choices[0].message.content, strict=False
            )
        except Exception as e:
            print("Encountered error when parsing JSON")
            print(e)
            return

        if self._save_plot:
            pattern = r"fig\.show\([^)]*\)"
            replacement = f"fig.write_image('./plots/{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png', engine='kaleido')"
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
                exec(code, {"pd": pd, "np": np, "px": px, "go": go}, local_namespace)

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
