
from helpers.email_sender import send_email
from openai import OpenAI
import json

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