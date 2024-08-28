import re
import string
import secrets
from pathlib import Path
from typing import Any, List, Dict
from dataclasses import dataclass
import pymupdf
import chromadb
from openai import OpenAI
from chromadb import Documents, EmbeddingFunction, Embeddings


@dataclass
class Document:
    text: str
    metadata: Dict


class pdfReader:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def pdf_to_docs(self, doc) -> List[str]:
        doc_list = []
        for page in doc:
            # breakpoint()
            page_blocks = page.get_text_blocks()
            for i, block in enumerate(page_blocks):
                txt_block = block[4]
                if "<image" in txt_block:
                    continue
                if re.search(r"^\d+$|^\s+$", txt_block) is not None:
                    continue
                if re.search("^[A-Z\s]+$", txt_block):
                    continue
                plc = re.search("([A-Z]{2,}\s{0,})+[a-z]{0,1}", txt_block)
                # if plc is not None:
                #     txt_block = txt_block[(plc.span()[1] - 2) :]
                if len(txt_block) <= 50:
                    continue
                txt_block = re.sub(r"\n", "", txt_block)
                txt_block = re.sub(r"\s+\d+\s{0,}$", "", txt_block)
                txt_block = re.sub(r"^\d+[.]\s{0,}", "", txt_block)
                txt_block = re.sub(r"^\s+|\s+$", "", txt_block)
                txt_block = re.sub(r"[^\w\s.,]", "", txt_block)
                txt_block = re.sub(r"\s{2}", " ", txt_block)

                # nb = str(page.number) + "_" + str(i)
                fn = self.file.stem + self.file.suffix
                dcc = Document(
                    text=txt_block,
                    metadata={
                        "page_number": page.number,
                        "paragraph_number": i,
                        "file_name": fn,
                    },
                )

                # dcc.excluded_embed_metadata_keys = ["page_number"]
                # dcc.excluded_llm_metadata_keys = ["page_number"]

                doc_list.append(dcc)

        return doc_list

    def load_data(self) -> List[str]:
        self.file = Path(self.file_path)
        with open(self.file_path, "rb") as f:
            doc = pymupdf.open(f, filetype="pdf")
        documents = self.pdf_to_docs(doc)
        return documents


def print_response(response) -> None:
    initial_text = "Found the following sources:\n\t********\n"
    for node in response.source_nodes:
        node_dict = node.to_dict()
        for k, v in node_dict["node"]["metadata"].items():
            initial_text = initial_text + "\t - " + str(k) + ": " + str(v) + "\n"
        initial_text = (
            initial_text + "\t - text: " + str(node_dict["node"]["text"]) + "\n"
        )
        initial_text = initial_text + "\t - score: " + str(node_dict["score"]) + "\n"
        initial_text = initial_text + "\n\t********\n"

    initial_text = initial_text + "\nAnswer:\n" + response.response

    print(initial_text)


def gen_id():
    alphabet = string.ascii_lowercase + string.ascii_uppercase
    id = "".join([secrets.choice(alphabet) for i in range(10)])
    return id


def print_chdb_resp(resp: dict) -> None:
    keys = ["ids", "distances", "metadatas", "documents"]
    n = len(resp["ids"][0])

    for i in range(n):
        for k in keys:
            print(f"{k: <10}: {resp[k][0][i]}")
        print("\n")


aiclient = OpenAI(api_key="sk-proj-gbWbt0aV8uWHOuRgnVwDT3BlbkFJmJbexpfzW9UrGDxlhG27")


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return aiclient.embeddings.create(input=[text], model=model).data[0].embedding


class OpenAiEmbed(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:

        print(input)

        embeddings = get_embedding(input[0])
        return embeddings


# class DbConnect:
#     def __init__(
#         self, db_name: str, embedding_fn: None | EmbeddingFunction = None
#     ) -> None:
#         self._client = chromadb.PersistentClient(db_name)
#         self.collection_names = [x.name for x in self._client.list_collections()]
#         self._embedding_fn = embedding_fn

#     # def _connect(self) -> None:
#     #     self._client = chromadb.PersistentClient(self._db_name)
#     #     self.collection_names = [x.name for x in self._client.list_collections()]

#     def create_collection(self, name) -> None:
#         try:
#             self._collection = self._client.create_collection(
#                 name=name, embedding_function=self._embedding_fn
#             )
#             self.current_collection = name

#         except Exception as e:
#             print("Problem encountered. See below: ... \n\n")
#             print(e)

#         self.collection_names = [x.name for x in self._client.list_collections()]

#     def set_collection(self, name):
#         try:
#             self._collection = self._client.get_collection(name=name)
#             self.current_collection = name

#         except Exception as e:
#             print("Problem encountered. See below: ... \n\n")
#             print(e)

#     def add_to_collection(self, documents: List[str | Document]):
#         n = len(documents)
#         for doc in documents:
#             if isinstance(doc, Document):
#                 self._collection.add(
#                     documents=doc.text, metadatas=doc.metadata, ids=gen_id()
#                 )
#             elif isinstance(doc, str):
#                 self._collection.add(documents=doc)
#             else:
#                 print(f"Document was not added: {doc}")

#     def query(self, query: str, n_results=3) -> Dict:

#         res = self._collection.query(query_texts=query)

#         n = len(res["ids"][0])

#         new_res = {}
#         for i in range(n):
#             new_res[i] = {
#                 "id": res["ids"][0][i],
#                 "distance": res["distances"][0][i],
#                 "metadata": res["metadatas"][0][i],
#                 "text": res["documents"][0][i],
#             }

#         return new_res
