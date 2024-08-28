import re
import sys
import inspect
import numpy as np
import pandas as pd

# import xml.etree.ElementTree as ET


def print_colored(text, color, end="\n"):
    colors = {
        "red": "\x1b[31m",
        "green": "\x1b[32m",
        "yellow": "\x1b[33m",
        "blue": "\x1b[34m",
    }
    reset = "\x1b[0m"
    sys.stdout.write(colors.get(color, "") + text + reset + end)


def mean_function(x: list) -> float:
    """Functions to compute the mean value of a vector.

    Args:
        x (list): a list of numeric values

    Returns:
        float: the average value
    """

    x = [x] if isinstance(x, (int, float)) else x

    return sum(x) / len(x)


def max_function(x: list) -> float:
    """Functions to compute the maximum value of a vector.

    Args:
        x (list): a list of numeric values

    Returns:
        float: the maximum value
    """
    x = list(x)

    return max(x)


def min_function(x: list) -> float:
    """Functions to compute the minimum value of a vector.

    Args:
        x (list): a list of numeric values

    Returns:
        float: the maximum value
    """
    x = list(x)

    return min(x)


def quantiles_function(x: list, quantiles: list) -> list:
    """Functions to compute the minimum value of a vector.

    Args:
        x (list): a list of numeric values

    Returns:
        list: list of quantiles
    """

    x = list(x)

    return list(np.quantile(x, quantiles))


def operations_function(target: str, operation: str | list[str], group: str = None):
    # df is implicit and comes from global enviroment

    if isinstance(operation, str):
        operation = [operation]

    res_dict = {target: []}
    # breakpoint()
    if group:
        fn = f"dff.groupby('{group}')"
        for o in operation:
            fn = fn + f"['{target}'].{o}()"
            try:
                ev = eval(fn)
                res_dict[target].append({o: ev})
            except Exception as e:
                print(e)
                print(f"There was an error. Check the function: {fn}")
    else:
        for o in operation:
            fn = f"dff['{target}'].{o}()"
            try:
                ev = eval(fn)
                res_dict[target].append({o: ev})
            except Exception as e:
                print(e)
                print(f"There was an error. Check the function: {fn}")

    return res_dict


def clean_dict(x: dict) -> dict:
    return {
        k: v
        for k, v in x.items()
        if (inspect.isclass(v) is False) and (inspect.ismodule(v) is False)
    }


def clean_answer(x: str) -> str:
    return re.sub("\s{0,}\\n\s{0,}", "\n", x)
