import re
import sys
import inspect
import pandas as pd
from pathlib import Path


def print_colored(text, color, end="\n"):
    colors = {
        "red": "\x1b[31m",
        "green": "\x1b[32m",
        "yellow": "\x1b[33m",
        "blue": "\x1b[34m",
    }
    reset = "\x1b[0m"
    sys.stdout.write(colors.get(color, "") + text + reset + end)


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
