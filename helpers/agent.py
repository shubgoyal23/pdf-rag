
from helpers.email_sender import send_email
from openai import OpenAI
import json
from langchain.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from helpers.milvus import insert_vector_data
client = OpenAI()

file = open("system_prompt.txt", "r")
system_prompt = file.read()
file.close()

tools = {
    "send_email": send_email
}

def chat(user_input: list[dict[str, str]]):
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    messages.extend(user_input)
    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=messages 
        )
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        parse_response = json.loads(response.choices[0].message.content)
        if parse_response.get("function"):
            tool = tools.get(parse_response.get("function"))
            resp = tool(parse_response.get("input"))
            if resp:
                messages.append({ "role": "assistant", "content": json.dumps({ "step": "observe", "content": "Email sent successfully" }) })
            else:
                messages.append({"role": "assistant", "content": json.dumps({ "step": "observe", "content": "Email failed to send" }) })
        if parse_response.get("step") == "output":
            return messages 
     
def pdf_upload(pdf_file: str):
    loader = PyPDFLoader(pdf_file)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
    )
    split_docs = text_splitter.split_documents(documents=docs)
    data = []
    for doc in split_docs:
        data.append({"pdf_id": doc.metadata.get("pdf_id"), "page": doc.metadata.get("page")})
    response = client.embeddings.create(
    input=[doc.page_content for doc in split_docs],
    model="text-embedding-3-small"
    )
    print(response.usage)
    for i in range(len(response.data)):
        data[i]["pdf_vector"] = response.data[i].embedding
    insert_vector_data(data)
    return True 