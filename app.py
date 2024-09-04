import io
import json
from pathlib import Path
from contextlib import redirect_stdout
import streamlit as st
from main import process_question, execute_code
from agents import save_plot_agent, check_api_key_agent
import plotly.io as pio

pio.templates.default = "plotly"

st.title("Analytics chat")


if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "valid" not in st.session_state:
    st.session_state.valid = False


def submit():
    st.session_state.api_key = st.session_state.widget
    st.session_state.widget = ""


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
    print(st.session_state.api_key)

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
        "Upload dataframe", type=["csv", "tsv"], accept_multiple_files=False
    )


# initializare istoric
if "messages" not in st.session_state:
    st.session_state.messages = []

# arata mesajele
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.text(message["content"])
        else:
            st.image(message["content"])

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
        try:
            # breakpoint()
            indent_response = process_question(question)

            check_plot_response = json.loads(save_plot_agent(indent_response).text)

            print("CODE CHECK FOR PLOT:\n", check_plot_response["answer"])

            if check_plot_response["is_plot"] == "true":
                execute_code(check_plot_response["answer"])
                path = sorted(Path("plots").glob("*.png"))[-1]
                st.session_state.messages.append(
                    {"role": "assistant", "content": str(path), "type": "plot"}
                )
                st.image(str(path))

            else:

                output_capture = io.StringIO()

                with redirect_stdout(output_capture):
                    execute_code(check_plot_response["answer"])

                captured_output = output_capture.getvalue()
                st.text(captured_output)
                st.session_state.messages.append(
                    {"role": "assistant", "content": captured_output, "type": "text"}
                )

        except Exception as e:
            print(e)
