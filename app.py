import io
import json
from pathlib import Path
from contextlib import redirect_stdout
import pandas as pd
import plotly.io as pio
import streamlit as st
import processor
from processor import process_question
from agents import save_plot_agent, check_api_key_agent

# otherwise black and white plots are displayed
pio.templates.default = "plotly"

# for checking the api key, set session variables
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "valid" not in st.session_state:
    st.session_state.valid = False


def submit():
    # api key session value takes the widget value
    st.session_state.api_key = st.session_state.widget
    st.session_state.widget = ""  # aftter that, delete the value from input widget


def refresh_df():
    # refresh df if the value in upload_file changes
    st.session_state.dff = pd.read_csv(st.session_state.uploaded_file)
    st.session_state.columns = st.session_state.dff.columns.to_list()  # refresh columns


st.title("Analytics chat")

with st.sidebar:
    st.header("Chat with your data")

    st.caption(
        "This software allows you to ask questions based on a dataframe you upload."
    )

    # input for api key
    st.text_input(
        "Gemini API key",
        type="password",
        placeholder="API KEY",
        key="widget",
        on_change=submit,
    )

    if st.session_state.api_key:
        # test if a call to the model is successful using the api key
        resp = check_api_key_agent(api_key=st.session_state.api_key)

        if resp == "invalid_key":
            st.markdown(""":red[The key is invalid. Try again]""")
        elif resp == "valid_key":
            st.markdown(""":green[The key is valid]""")
            st.session_state.valid = True
        elif resp == "empty_key":
            st.markdown(""":orange[The key is empty]""")
        else:
            st.markdown(f""":orange[{resp}]""")

    # upload csv file
    st.file_uploader(
        "Upload dataframe",
        key="uploaded_file",
        type=["csv"],
        accept_multiple_files=False,
        on_change=refresh_df,
    )


# initialize the history of the chat. all messages go here
if "messages" not in st.session_state:
    st.session_state.messages = []

# show the history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.text(message["content"])
            if message.get("code"):
                st.code(message.get("code"))
        else:
            st.image(message["content"])  # display image
            if message.get("code"):
                st.code(message.get("code"))

# while the api key is not valid or missing, the chat is blocked
if prompt := st.chat_input(
    "What do you want to know?", disabled=(not st.session_state.valid)
):
    # user asking
    with st.chat_message("user"):
        st.markdown(prompt)

    # put the message in the history
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "type": "text"}
    )

    # assistent response
    with st.chat_message("assistant"):
        # take question from user
        question = prompt

        # initialize dff and columns variables
        if "dff" in st.session_state and "columns" in st.session_state:
            dff = st.session_state.dff
            columns = st.session_state.columns

        try:
            # get the response from LLM
            indent_response = process_question(question, columns)

            # check is the code genetates a plot. if so, the plot is saved
            check_plot_response = json.loads(
                save_plot_agent(indent_response).text, strict=False
            )

            print("CODE CHECK FOR PLOT:\n" + check_plot_response["answer"])

            # if the code generates plot
            if check_plot_response["is_plot"] == "true":
                exec(check_plot_response["answer"])
                # take the last path from the folder and update history
                path = sorted(Path("plots").glob("*.png"))[-1]
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": str(path),
                        "type": "plot",
                        "code": check_plot_response["answer"],
                    }
                )
                # show the code and plot now
                st.image(str(path))
                st.code(check_plot_response["answer"])

            else:
                # if it is not plot, capture print statement
                output_capture = io.StringIO()

                with redirect_stdout(output_capture):
                    exec(check_plot_response["answer"])

                captured_output = output_capture.getvalue()

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": captured_output,
                        "type": "text",
                        "code": check_plot_response["answer"],
                    }
                )
                st.text(captured_output)
                st.code(check_plot_response["answer"])

            # refresh session variable if dff of columns were changed
            st.session_state.dff = dff
            st.session_state.columns = dff.columns.to_list()

        except Exception as e:
            print(e)
