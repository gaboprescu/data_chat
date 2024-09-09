# Chat with your data | Data confident
## About

The objective is to give users the posibility to analyse a dataset without writing code or using a dedicated tool for data analytics. Just ask a question or create a task and the program will respond.

And most importat, the data frame is NOT sent to the LLM.

## How it works
You need two thing to start chating with your data: a CSV file and an API Key from Gemini.

Once you have those, you can start asking questions. 

What can you ask? A lot of stuff, from column names, to creating statistics, changing column, to creating plots and even generating ML models.

## What is the catch
You might argue that Claude can offer the same thing. The difference here is that you keep the confidentiality of the data. In other word, you do not send the data to the LLM. The only thing you send are the column names and that is it. The dataframe and the results are only are not seen by the LLM.

## Techinical details
The project works by prompting a LLM which generates code. The code is executed in the environmet and it is applied to your dataframe. 

The LLM used is *gemini-1.5-flash*. For future development, other models can be included, especially models that focus on generating code.


### Structure

The main file is [processor.py](processor.py) which contains the function `process_question()`. This function takes as arguments the question and a list with column names.

Inside the `process_question()` another two agents are called: `function_creation_agent()` and `indent_agent()`. The agents are in [agents.py](agents.py) file.

An agent is just a function that does a very specific task by calling a LLM.

`function_creation_agent()` tells the LLM that it is a data analyst and the job is to create code so it will respond to the user's questions. Each agent has a also a predefined prompt template where the task is detailed and restrictions are imposed. The prompt template evolves quite fast because with each new question a users asks, it needs to be refined so the answer will be the expected one. LLM are probabilistic and through prompt enginering we want to make it as deterministic as possible. For this angent, the prompt template is `function_creation_template()` from [templates.py](templates.py).

The response from `function_creation_agent()`, if everything went well, is either a code snippet of `false`. `false` is retuned when the question or task send by user is not about the dataframe in hand. The user will be asked for another question.

If the response is a code snippet, then it is passed to `indent_agent()` who is responsible for optimizing the code and creating the appropiate indent, so it will be executed without any errors.

Around `process_question()` everything else is cosntructed.

Inside [processor.py](processor.py) a `while` loop serves as a frame for continous demanding questions from the user. 

After the user send a question, the question is processed by `process_question()`. The response is then executed in the Python environment and the output is captured and displayed in the Terminal. The output can be either text or plot. In case of a plot, a browser window is opened to diplay it.

### How to run it

Before starting the program, you must have the Gemini API Key. Place it in the [.config](.config) file without quotes.

To start the program just use `python processor.py`. The interaction will be made in the Terminal window. 

For demonstration purpose, a dataframe is already loaded, so you do not have to upload one. Just start asking to discover it.

The program does not have much error handling at this moment, so if the execution encounters error, it might end. Only a few errors are captured and handled.

Press CTRL+C to end the execution.

If you want to upload you own dataframe, go to the interface.

### The interface

A Streamlit application was also created to make the program more visual appealing. To start the Streamlit app, use the command `streamlit run app.py`.

Inside the interface, make sure to first add a valid API Key and a dataframe in CSV format. The caht is blocked until you provide a valid API Key for Gemini.

## What can you ask

This is just a list of usual question asked or tasked performed during a Data Science project. Do not limit to this list an come with oyur use cases.

1. What are the column (variable) names (print each one under the other).
2. Clean the column names. Replace spaces and special characters with underscore.
3. Show the first row of the table.
4. Show the first rows of the table.
5. What types are the variables
6. Make a description of the table. <span style="color:yellow">Problem! Does not know how to add include="all" as argument</span>
7. How many missing values each variables has. (Sort them)
8. Which are the numeric variables <span style="color:yellow">Problem! Assumes by looking at variable name, not testing with code</span>
9.  What are the object variables.
10. Create a box plot for each numeric variable <span style="color:yellow"> Problem! Might have to rephrase a bit. Agains assumes which varaibles are numeric.</span>
11. What is the correlation for numeric variables. <span style="color:yellow">Problem! Assumes by looking at variable name, not testing with code</span>
12. Create a corr plot for numeric variables.
13. How many uniques values each object variable has.
14. Count the number of unique values by each variable.
15. Create a box plot for a <numeric_variable> split by <object_variable>. (use any combination).
16. Check if there is a significant difference between the average <numeric_varaible> split by <object_variable>.
17. Any other statistic test. (numeric split by object)
18. Check outliers for numeric variables. (put different limits)
19. Remove the outliers.
20. Standardize the <numeric_variable> and save it with a separate name.
21. Transform <object_variable> into one hot encoding (give details on how to do it)
22. Remove variables.
23. Create a certain ML model. Use <variable> as label. <span style="color:yellow">Problem! The Json respons might not be well formated.</span>

