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

pio.templates.default = "plotly"


def execute_code(code):  # este aici ca sa poata sa ia variabilele direct din global
    exec(code)


if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "valid" not in st.session_state:
    st.session_state.valid = False


def submit():
    st.session_state.api_key = st.session_state.widget
    st.session_state.widget = ""


def refresh_df():
    st.session_state.dff = pd.read_csv(st.session_state.uploaded_file)
    st.session_state.columns = st.session_state.dff.columns.to_list()


st.title("Analytics chat")

with st.sidebar:
    st.header("Interact with you data")

    st.caption(
        "This software allows you to ask questions based on dataframe you upload."
    )

    st.text_input(
        "Gemini API key",
        type="password",
        placeholder="API KEY",
        key="widget",
        on_change=submit,
    )

    if st.session_state.api_key:

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

    st.file_uploader(
        "Upload dataframe",
        key="uploaded_file",
        type=["csv", "tsv"],
        accept_multiple_files=False,
        on_change=refresh_df,
    )


# initializare istoric
if "messages" not in st.session_state:
    st.session_state.messages = []

# arata mesajele
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.text(message["content"])
            if message.get("code"):
                st.code(message.get("code"))
        else:
            st.image(message["content"])
            if message.get("code"):
                st.code(message.get("code"))

# reactie la input

if prompt := st.chat_input("What is up", disabled=(not st.session_state.valid)):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt, "type": "text"}
    )

    # response = f"Echo {prompt}"
    # raspunsul asistentului
    with st.chat_message("assistant"):
        question = prompt

        if "dff" in st.session_state and "columns" in st.session_state:
            dff = st.session_state.dff
            columns = st.session_state.columns

        try:
            # breakpoint()
            print("THE COLUMNS:\n", columns)
            indent_response = process_question(question, columns)

            check_plot_response = json.loads(
                save_plot_agent(indent_response).text, strict=False
            )

            print("CODE CHECK FOR PLOT:\n" + check_plot_response["answer"])

            if check_plot_response["is_plot"] == "true":
                exec(check_plot_response["answer"])
                path = sorted(Path("plots").glob("*.png"))[-1]
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": str(path),
                        "type": "plot",
                        "code": check_plot_response["answer"],
                    }
                )
                st.image(str(path))
                st.code(check_plot_response["answer"])

            else:

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

            st.session_state.dff = dff
            st.session_state.columns = dff.columns.to_list()

        except Exception as e:
            print(e)
