import io
import json
import os
from pathlib import Path
from contextlib import redirect_stdout
import pandas as pd
import plotly.io as pio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import streamlit as st
from reason_agents import DfCodeAgent, DfOaCodeAgent
from functions import check_api_key

# otherwise black and white plots are displayed
pio.templates.default = "plotly"

# for checking the api key, set session variables
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "valid" not in st.session_state:
    st.session_state.valid = False

if "key_resp" not in st.session_state:
    st.session_state.key_resp = ""

if "df" not in st.session_state:
    st.session_state.df = None


def submit():
    # api key session value takes the widget value
    st.session_state.api_key = st.session_state.widget
    # st.session_state.widget = ""  # aftter that, delete the value from input widget


def refresh_df():
    # refresh df if the value in upload_file changes
    st.session_state.df = pd.read_csv(st.session_state.uploaded_file)
    st.session_state.columns = st.session_state.df.columns.to_list()  # refresh columns


st.title("Analytics chat")

with st.sidebar:
    st.header("Chat with your data")

    st.caption(
        "This software allows you to ask questions based on a dataframe you upload."
    )

    select_llm = st.selectbox(
        "How would you like to be contacted?", ("openai", "gemini")
    )

    # input for api key
    st.text_input(
        "API key",
        type="password",
        placeholder="API KEY",
        key="widget",
        on_change=submit,
    )

    if st.session_state.api_key:
        # test if a call to the model is successful using the api key
        st.session_state.key_resp = check_api_key(
            api_key=st.session_state.api_key, which=select_llm
        )

        if st.session_state.key_resp == "invalid_key":
            st.markdown(""":red[The key is invalid. Try again]""")
        elif st.session_state.key_resp == "valid_key":
            st.markdown(""":green[The key is valid]""")
            st.session_state.valid = True
        elif st.session_state.key_resp == "empty_key":
            st.markdown(""":orange[The key is empty]""")
        else:
            st.markdown(f""":orange[{st.session_state.key_resp}]""")

    # upload csv file
    st.file_uploader(
        "Upload dataframe",
        key="uploaded_file",
        type=["csv"],
        accept_multiple_files=False,
        on_change=refresh_df,
    )

if st.session_state.key_resp == "valid_key":
    if st.session_state.df is not None:
        if select_llm == "openai":
            cda = DfOaCodeAgent(
                st.session_state.df,
                api_key=st.session_state.widget,
                save_plot=False,
                model="gpt-4o",
                diagnostics=True,
            )
        if select_llm == "gemini":
            cda = DfCodeAgent(
                st.session_state.df, api_key=st.session_state.widget, save_plot=False
            )


# initialize the history of the chat. all messages go here
if "messages" not in st.session_state:
    st.session_state.messages = []

# show the history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            if message.get("content"):
                st.markdown(message["content"])
            if message.get("code_output"):
                st.text(message["code_output"])
            if message.get("code"):
                st.code(message.get("code"))
            if message.get("explanation"):
                st.markdown(message.get("explanation"))
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
        # breakpoint()
        # take question from user
        question = prompt

        plot_start = len(os.listdir("./app/plots"))
        try:
            # get the response from LLM
            resp = cda.generate_content(question)

            plot_stop = len(os.listdir("./app/plots"))

            if plot_stop > plot_start:

                plot_start = plot_stop

                path = sorted(Path("./app/plots").glob("*.png"))[-1]

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": str(path),
                        "type": "plot",
                        "code": resp["model"]["answer"],
                    }
                )
                # show the code and plot now

                st.image(str(path))

                st.code(resp["answer"])

            else:

                if resp["model"]["answer"] == "no code":
                    # print(resp["model"]["explanation"])
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "text",
                            "content": resp["model"]["explanation"],
                        }
                    )
                    st.markdown(resp["model"]["explanation"])
                    # st.code(resp["answer"])
                else:

                    if resp.get("code_run"):

                        if resp["code_run"].get("output") is not None:
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "type": "text",
                                    "code_output": resp["code_run"]["output"],
                                    "code": resp["model"]["answer"],
                                    "explanation": resp["model"]["explanation"],
                                }
                            )
                            st.text(resp["code_run"]["output"])
                            st.code(resp["model"]["answer"])
                            st.markdown(resp["model"]["explanation"])
                        else:
                            # print(resp["code_run"]["exception"])
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "type": "text",
                                    "code_output": resp["code_run"]["output"],
                                    "code": "",
                                    "explanation": resp["model"]["explanation"],
                                }
                            )
                            st.text(resp["code_run"]["exception"])
                            st.code(resp["model"]["answer"])
                            st.markdown(resp["model"]["explanation"])

        except Exception as e:
            print(e)
