from string import Template

function_creation_template = Template(
    """You are given a dataframe called "dff".
    The dataframe contains the following columns: $columns .\n

    Answer the question delimited by #### by creating a script in Python.\n

    At the end of the script make sure to print the results.\n

    Use only Python standard packages, Pandas, Numpy. To create graph and plots use Plotly package.\n

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
    """You are given a task and a snippet of Python code.\n 
    Bothe the code and the task are delimited by ####.\n
    You job is to check if the code solves the task. Check the code for correctness and redo the indentation.\n

    The answer will be in JSON format using the template:\n
    {"answer": "code"}

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
