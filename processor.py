from argparse import ArgumentParser
from functions import read_table
from reason_agents import DfOaCodeAgent

parser = ArgumentParser(prog="Data Chat")
parser.add_argument("filename", help="The path for CSV file")
parser.add_argument("api_key", help="OpenAI api key")
parser.add_argument("-m", "--model", help="Default is gpt-4o-mini")
args = parser.parse_args()


def cycle_message(dff) -> None:
    """Create a cycle where the user asks a question and the program responds."""

    cda = DfOaCodeAgent(dff, api_key=args.api_key)
    

    try:
        while True:

            question = input("\n\nAsk a question about the data:\n")

            # empty questions are not accepted
            if question == "" or question is None:
                continue
            resp = cda.generate_content(question)

            # print(resp)

            if resp["model"]["answer"] == "no code":
                print(resp["model"]["explanation"])
            else:
                if resp.get("code_run"):
                    if resp["code_run"].get("output") is not None:
                        print(resp["code_run"]["output"])
                    else:
                        print(resp["code_run"]["exception"])

    except KeyboardInterrupt:
        print("\nBye bye!")


def main():
    # create data
    dff = read_table(args.filename)
    cycle_message(dff)


if __name__ == "__main__":
    main()
