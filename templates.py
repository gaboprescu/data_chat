from string import Template

function_creation_template = Template(
    """You are given a dataframe called "dff".
    The dataframe contains the following columns: $columns .\n

    Answer the question delimited by #### by creating a script in Python.\n

    Use the next rules to generate the code:/n
    1. Do not assume any information about the data or columns. Check information using Python code.
    Example: if there is column called gender, do not assume the the values are "female" and "male". Check the information.\n

    2. At the end of the script make sure to print the results.\n

    3. Use only Python standard packages, Pandas, Numpy, Scikit-Learn, SciPy . To create graph and plots use Plotly package.\n

    The answer will be in JSON format using the template:\n

    {"answer": "script"}

    If the question does not refer to the dff dataframe, return the next answer:\n

    {"answer": "false"}

    Do not add comments or explanations.

    Question: 
    ####
    $question
    #### \n


    Use the next example:\n

    Question: What is the average salary?\n
    Response:\n
    {"answer": "mn = dff['salary'].mean()\n print(nm)"}\n

    Question: How heavy is the largest fish?\n
    Response:\n
    {"answer": "false"}

    """
)

indent_template = Template(
    """You are given a task and a script in Python.\n 
    Both the the script and the task are delimited by ####.\n
    You job is to check if the script solves the task. 
    Use the following information to perform the job:\n
    1. Assume "dff" data frame is already loaded in the environment, so do not create it.\n
    2. Check if the script solves the task.\n
    3. Redo the indentation.\n
    4. Do not add any lines of code unless it is strictly necessary.\n
    5. If there is nothing to add, return the script as you received it.\n

    The answer will be in JSON format using the template:\n
    {"answer": <code>}

    Code:\n
    ####$code#### \n

    Task:\n
    ####$task#### \n


    Use the follwing example:
    Task: create a function that adds two numbers.
    Code: "def fn(a, b): z = a+b return z"
    Answer: {"answer": "def fn(a, b):\n\tz = a + b\n\treturn z"}
    """
)

save_plot_template = Template(
    """You receive a script in Python. The script is delimited by ####./n

    If the script contains code that creates and displays a plot, your job is to modify the script. 
    Rather than displaying, save the plot using the next template as name: ./plots/<current_time>.png ./n

    If the script does not contain code for creating a plot, do not make any changes to it. /n

    The response must be returned as a JSON with the next template:
    {"answer": <code>, "changed": "true" or "false", "is_plot": "true" or "false"} /n

    Script:\n
    ####
    $script
    ####

    Use the next examples:\n
    Example 1:\n
    Script: "import plotly.graph_objects as go
    fig = go.Figure(data=[go.Pie(labels=df_age['index'], values=df_age['age'], hole=0.3)])
    fig.show()"\n
    Response:
    {"answer": "import plotly.graph_objects as go
    from datetime import datetime
    fig = go.Figure(data=[go.Pie(labels=df_age['index'], values=df_age['age'], hole=0.3)])
    fig.write_image(f'./plots/{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.png', engine='kaleido')",
    "changed": "true",
    "is_plot": "true"}\n

    Example 2:\n
    Script: "print('hello')"\n
    Response:
    {"answer": "print('hello')",
    "changed": "false",
    "is_plot": "false"}

"""
)


### INSERARE TIP DE COLOANE
