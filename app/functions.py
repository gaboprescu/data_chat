import re
import sys
import inspect
from typing import Literal
from pathlib import Path
import pandas as pd
from openai import OpenAI
import google.generativeai as genai


def print_colored(text, color, end="\n"):
    colors = {
        "red": "\x1b[31m",
        "green": "\x1b[32m",
        "yellow": "\x1b[33m",
        "blue": "\x1b[34m",
    }
    reset = "\x1b[0m"
    print(colors.get(color, "") + text + reset + end)


def clean_dict(x: dict) -> dict:
    return {
        k: v
        for k, v in x.items()
        if (inspect.isclass(v) is False) and (inspect.ismodule(v) is False)
    }


def clean_answer(x: str) -> str:
    return re.sub("\s{0,}\\n\s{0,}", "\n", x)


def read_table(pth):
    pth = Path(pth)

    if pth.suffix == ".csv":
        if pth.exists():
            df = pd.read_csv(pth)
        else:
            raise FileExistsError(f"The file {pth} is not there")
    else:
        raise ValueError(f"The file {pth} is not csv")

    return df


def check_api_key(api_key: str, which: Literal["openai", "gemini"]) -> str:
    """Agent to check if the API key is valid. Make a a simple request to the model and
    depending on the answer it is determined if the key is valid.

    Args:
        api_key (str): api key for gemini

    Returns:
        str: empty_key | valid_key | invalid_key | error
    """

    if api_key == "":
        return "empty_key"

    if which == "openai":
        client = OpenAI(api_key=api_key)
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Tell me joke"}],
            )
            return "valid_key"
        except Exception as e:
            if e.status_code == 401:
                return "invalid_key"
            else:
                return f"There was an error: {e}"

    elif which == "gemini":
        genai.configure(api_key=api_key)

        client = genai.GenerativeModel(
            "gemini-1.5-flash",
        )

        try:
            resp = client.generate_content("Tell me a joke")
            return "valid_key"
        except Exception as e:
            if e.reason == "API_KEY_INVALID":
                return "invalid_key"
            else:
                return f"There was an error: {e}"

    else:
        return "For 'which' arguments chose openai or gemini"


def process_json(jsn):

    jsn = str(jsn)

    jsn = re.sub("```\s{0,}json", "", jsn)
    jsn = re.sub("```", "", jsn)
    jsn = re.sub('"{3}', '"', jsn)
    jsn = re.sub("^\(", "", jsn)
    jsn = re.sub("\)$", "", jsn)
    # jsn = regex.sub(
    #     r"""(?<!\{\s*|\s*:\s*|(a-z)\s*,\s*|"\s*,\s*)"\s*(?!\s*\}|\s*:\s*|\s*,\s*)""",
    #     "'",
    #     jsn,
    # )

    return jsn


def replace_figure(text):

    main_pattern = r"fig\.show\([^)]*\)"
    with_space_pattern = r"[ ]{0,}fig\.show\([^)]*\)"
    space_pattern = r"[ ]{0,}"

    sp = re.search(with_space_pattern, text)

    if sp is None:
        return text

    sp = sp.span()
    short_text = text[sp[0] : sp[1]]

    sp = re.search(space_pattern, short_text).span()
    space = short_text[sp[0] : sp[1]]

    replacement = (
        "with open('./app/plots/temp_fig.json', 'w') as f:\n"
        + space
        + "        f.write(fig.to_json(pretty=True))"
    )

    text = re.sub(main_pattern, replacement, text)

    return text
