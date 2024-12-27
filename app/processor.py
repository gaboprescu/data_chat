from pprint import pprint
from argparse import ArgumentParser
from functions import read_table
from reason_agents import DfOaCodeAgent, InferColsAgent, GenerateQuestionsAgent

parser = ArgumentParser(prog="Data Chat")
parser.add_argument("filename", help="The path for CSV file")
parser.add_argument("api_key", help="OpenAI api key")
parser.add_argument("-m", "--model", help="Default is gpt-4o-mini")
args = parser.parse_args()
# USE a short description of the table before asking.


def cycle_message(dff) -> None:
    """Create a cycle where the user asks a question and the program responds."""

    cda = DfOaCodeAgent(dff, api_key=args.api_key, diagnostics=False)
    ica = InferColsAgent(dff, api_key=args.api_key, show_diagnostics=False)
    gqa = GenerateQuestionsAgent(api_key=args.api_key, show_diagnostics=False)

    tbl_desc = input(
        "\nGive a description of table, what it represents and what is inside:\n"
    )

    # generate coloumn description and suggestions
    inf_resp = ica.infer_cols(tbl_desc)
    if inf_resp:
        if inf_resp.get("column_description"):
            col_desc = inf_resp.get("column_description")
            print("Cols description:\n")
            pprint(col_desc)
        else:
            print("The model did not infer over the column description")
        if inf_resp.get("suggestions"):
            suggestions = inf_resp.get("suggestions")
            print("Suggestions:\n")
            pprint(suggestions)
        else:
            print("The model did not infer over the column suggestions")
    else:
        print("No description or sugestion was created the program will continue.")

    # generate questions
    gqa_resp = gqa.generate_qustions(
        tbl_desc=tbl_desc,
        col_desc=col_desc,
        col_types=dff.dtypes.apply(lambda x: str(x)).to_dict(),
    )

    if gqa_resp:
        print("\n\nHere are some questions that you can ask about the data:\n")
        pprint(gqa_resp)
    else:
        print("\nNo questions were generated\n")

    try:
        while True:

            question = input("\n\nAsk a question about the data:\n")

            # empty questions are not accepted
            if question == "" or question is None:
                continue
            resp = cda.generate_content(question, tbl_desc, col_desc)

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
