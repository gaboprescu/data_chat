from argparse import ArgumentParser
from functions import read_table
from reason_agents import DfOaCodeAgent

parser = ArgumentParser(prog="Data Chat")
parser.add_argument("filename", help="The path for CSV file")
parser.add_argument("api_key", help="OpenAI api key")
parser.add_argument("-m", "--model", help="Default is gpt-4o-mini")
args = parser.parse_args()
# USE a short description of the table before asking.


def cycle_message(dff) -> None:
    """Create a cycle where the user asks a question and the program responds."""

    cda = DfOaCodeAgent(dff, api_key=args.api_key, diagnostics=True)

    tbl_desc = input(
        "\nGive a description of table, what it represents and what is inside:\n"
    )

    try:
        while True:

            question = input("\n\nAsk a question about the data:\n")

            # empty questions are not accepted
            if question == "" or question is None:
                continue
            resp = cda.generate_content(question, tbl_desc)

            # print(resp)
            # breakpoint()
            if resp:
                if resp.get("model"):
                    if resp.get("model").get("answer"):
                        if resp["model"]["answer"] == "no code":
                            print(resp["model"]["explanation"])
                        else:
                            if resp.get("code_run"):
                                if resp["code_run"].get("output"):
                                    print(resp["code_run"]["output"])
                                if resp["code_run"].get("exception"):
                                    print(resp["code_run"]["exception"])
                    else:
                        print("\nAnswer key is missing\n")
                else:
                    print("\nModel key is missing\n")
            else:
                print("\nNo response was returned\n")
    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    # create data
    dff = read_table(args.filename)
    cycle_message(dff)


if __name__ == "__main__":
    main()
