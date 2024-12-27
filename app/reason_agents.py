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
from wordcloud import WordCloud

# sys.path.insert(0, "./app")
from functions import print_colored, process_json, replace_figure


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
        -- **description of the table
        -- **description of the columns
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
    - **Wordcloud

    
    # Output format for success response:
    
    Produce a response with the following template:

    {"answer": <the_valid_python_code>. 
    "explanation": <a_few_details_on_how_the_response_generated>}
    
    # Output format when problems are identified:

    If you any of the next situation occur:
    - **The question is not refering to the dataframe.
    - **The question refers to previous questions or results and that information is not available.
    
    Use this template:

    {"answer": "no code", 
    "explanation": <a_few_details_on_how_the_response_generated>}

    
    # Recommendations on generating code:

    - **The code generated must be syntactical correct and run without any errors.
    - **Do not assume anything about the values found in the columns. 
    - **Do not use double quotes inside the keys or the values of the response. Otherwise it cannot be parsed as JSON.
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

    AGENT_INSTRUCTION = AGENT_INSTRUCTION

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
        # self.system_instruction = AGENT_INSTRUCTION
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
            system_instruction=self.AGENT_INSTRUCTION,
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
                    {
                        "pd": pd,
                        "np": np,
                        "px": px,
                        "go": go,
                        "plt": plt,
                        "WordCloud": WordCloud,
                    },
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

    AGENT_INSTRUCTION = AGENT_INSTRUCTION

    def __init__(
        self,
        df,
        api_key,
        model="gpt-4o",
        save_plot=False,
        keep_history=False,
        diagnostics=False,
        check_history=False,
    ) -> None:
        self.dff = df.copy()
        # self.system_instruction = system_instruction
        self._create_client(api_key)
        self.model = model
        # self.system_instruction = AGENT_INSTRUCTION
        self._diagnostics = diagnostics
        self._check_history = check_history
        self._keep_history = check_history | keep_history
        self._save_plot = save_plot
        self.history = []

    def _create_client(self, api_key):

        self.code_client = OpenAI(api_key=api_key)

    def generate_content(self, question, tbl_desc=None, col_desc=None):

        question_with_args = """Question: {}. Additional information: {}"""
        question_with_hist = (
            """Question: {}. Additional information: {}. Conversation history: {}."""
        )

        add_args = json.dumps(
            {
                "columns": self.dff.columns.to_list(),
                "dtypes": self.dff.dtypes.apply(lambda x: str(x)).to_dict(),
                "table_description": tbl_desc,
                "columns_description": col_desc,
            }
        )

        if self._check_history:

            self.response = self.code_client.chat.completions.create(
                model=self.model,
                temperature=1,
                top_p=1,
                messages=[
                    {"role": "system", "content": self.AGENT_INSTRUCTION},
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
                    {"role": "system", "content": self.AGENT_INSTRUCTION},
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
            # pattern = r"fig\.show\([^)]*\)"
            # # replacement = f"fig.write_image('./app/plots/{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png', engine='kaleido')"
            # replacement = "with open('./app/plots/temp_fig.json', 'w') as f:\n        f.write(fig.to_json(pretty=True))"
            # self.response["answer"] = re.sub(
            #     pattern, replacement, self.response["answer"]
            # )
            self.response["answer"] = replace_figure(self.response["answer"])

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
                    {
                        "pd": pd,
                        "np": np,
                        "px": px,
                        "go": go,
                        "plt": plt,
                        "WordCloud": WordCloud,
                    },
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


AGENT_INFER = """

# Initial setup
You receive:
- **The description of the table or dataframe.
- **The list of column names.
- **The types of the columns.

# Your job
Generate a descriptive interpretation of the list of column names.
Also look for possibble missmatch between the column name and the column type.

Consider the common meanings and uses for each column name, along with potential related data types or contents. Use your knowledge to infer plausible data descriptions that would align with typical usage in databases or datasets.

# Steps

1. **Analyze Column Names**: For each column name, break it down to understand its components and context.
2. **Infer Possible Descriptions**: Based on common terminology, suggest what type of data or information the column might contain.
3. **Synthesize Descriptions**: Formulate a clear and concise description for each column, reflecting possible real-world uses.
4. **Output**: Compile the descriptions into a coherent response.

# Output Format

Provide a description for each column in a bulleted list format. Each description should be a complete sentence briefly explaining the potential content or purpose of the column.

# Example

Input:
{
    "table_description": "The table contains information about the users and their transactions in the shop",
    "column_names": ["user_id","transaction_date", "product_cost"],
    "column_types": {"user_id": "object", "transaction_date": "object", "product_cost": "object"}
 }

Output:
{
    "column_description": {
        "user_id": "A unique identifier assigned to each user in the database, typically a string or integer.",
        "transaction_date": "The specific date when a transaction occurred, generally formatted as a date type.",
        "product_cost": "Represents the monetary cost of each product, usually stored as a decimal or float value".
    },
    "suggestions": "Column 'product_cost' should be of type numeric"    
}

# Notes

- If a column name is ambiguous, provide the most logical description based on common data practices.
- If the column names indicate time or sequencing, mention their typical data formats.
- If the column names seems to be a random string, point that out.
"""


class InferColsAgent:

    AGENT_INFER = AGENT_INFER

    def __init__(self, df, api_key, model="gpt-4o", show_diagnostics=True):
        self.cols = df.columns.to_list()
        self.col_types = df.dtypes.apply(lambda x: str(x)).to_dict()
        self._create_client(api_key)
        self._model = model
        self.show_diagnostics = show_diagnostics

    def _create_client(self, api_key):

        self._info_client = OpenAI(api_key=api_key)

    def infer_cols(self, tbl_desc=None):

        msg = {
            "table_description": tbl_desc,
            "column_names": self.cols,
            "column_types": self.col_types,
        }

        msg = json.dumps(msg)

        try:
            self.response = self._info_client.chat.completions.create(
                model=self._model,
                temperature=1,
                top_p=1,
                messages=[
                    {"role": "system", "content": self.AGENT_INFER},
                    {"role": "user", "content": msg},
                ],
            )

            self.response = json.loads(
                self.response.choices[0].message.content, strict=False
            )

            if self.show_diagnostics:
                print_colored(self.response, color="yellow")

            return self.response

        except Exception as e:
            print(e)
            print(
                """The agent who infers the column description encountered the error above.
                You can continue as is, or restart to be able to pass more info."""
            )


# - **Predictive or Inferential Analysis**: Frame questions that might be answered through predictive models or inferential statistics.

AGENT_QUESTION = """
Generate possible analytics questions based on the provided information about a table. 
Your questions should focus on meaningful insights or analysis that can be derived from the data.

# Steps

1. **Understand the Data Structure**: Review the description of the table, including the column names, their data types, and descriptions. This will help you understand the relationships and potential for analysis within the dataset.
   
2. **Identify Key Variables**: Note columns that are likely to be of particular interest due to their potential impact, variability, or business relevance.

3. **Formulate Questions**:
   - **Descriptive Analysis**: Ask questions that explore the basic characteristics of the data, such as summary statistics or distribution patterns.
   - **Visual Analysis**: Create plots to hightlight different chracteristics of the data.
   - **Comparative Analysis**: Develop questions that involve comparing different groups or relationships within the data.
   - **Trend Analysis**: Consider potential timelines or sequences that could be analyzed for trends or changes over time.
   
# Output Format
- Each question should be concise and focus on potential insights or analysis.
- Do not insert in the questions and array of columns. Focus on one aspect at a time.
- Output a json object with the following structure:

{"1": "Question 1", "2": "Question 2", ...}

# Examples

**Input**: 
- Table Description: Information about customer purchases in an e-commerce store.
- Columns:
  - Customer_ID (integer): Unique identifier for each customer.
  - Purchase_Amount (decimal): Total amount of each purchase.
  - Purchase_Date (datetime): Date and time of the purchase.
  - Product_Category (string): Category of the purchased product.
  - Payment_Method (string): Method used to make the payment.

**Output**:
{
"1": "What is the average purchase amount spent by each customer?",
"2": "How does the purchase amount differ across various product categories?",
"3": "What is the trend in purchase amounts over time?",
"4": "Which payment method is most commonly used for high-value purchases?",
"5": "Do purchase amounts significantly differ between different customer segments based on purchase frequency?"
} 

# Notes

- Consideration for different types of analysis ensures comprehensive exploration of the dataset's potential insights.
- Avoid questions that require data not described in the columns or clearly unrelated to the provided data.
- Avoid questions that involve a large number of columns or complex operations.
- Adjust the complexity or simplicity of questions based on the available data and its descriptions.
- Where possible, propose graphics and plots that could help answer the questions.
"""


class GenerateQuestionsAgent:

    AGENT_QUESTION = AGENT_QUESTION

    def __init__(self, api_key, model="gpt-4o", show_diagnostics=True):
        self._create_client(api_key)
        self._model = model
        self.show_diagnostics = show_diagnostics

    def _create_client(self, api_key):

        self._info_client = OpenAI(api_key=api_key)

    def generate_qustions(self, tbl_desc=None, col_desc=None, col_types=None):

        msg = {
            "Table description": tbl_desc,
            "Column description": col_desc,
            "Column types": col_types,
        }

        msg = json.dumps(msg)

        try:
            self.response = self._info_client.chat.completions.create(
                model=self._model,
                temperature=1,
                top_p=1,
                messages=[
                    {"role": "system", "content": self.AGENT_QUESTION},
                    {"role": "user", "content": msg},
                ],
            )

            self.response = json.loads(
                self.response.choices[0].message.content, strict=False
            )

            if self.show_diagnostics:
                print_colored(self.response, color="yellow")

            return self.response

        except Exception as e:
            print(e)
            print(
                """The agent who infers questions encountered the error above.
                You can continue as is, or restart."""
            )
