from fastapi import FastAPI , Request
from fastapi.responses import Response
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os , csv
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
app = FastAPI()
user = {}
chat = ChatGoogleGenerativeAI(model = "gemini-2.5-flash",google_api_key=api_key)

def response_llm(user_msg):
    prompt = f"""{user_msg}  : give reply like a human and it should be concise and give reply in hindi with roman english and dont use pure hindi words """
    result = chat.invoke(prompt)
    return result.content

def send_reply(message):
    twilio_response = MessagingResponse()
    twilio_response.message(message)
    return Response(
        content = str(twilio_response),
        media_type = "application/xml"
    )

@app.post("/webhook")
async def whatsapp_webhook(request:Request):
    form_data = await request.form()
    user_msg = form_data.get("Body")
    user_number = form_data.get("From")
    if user_msg.lower() == "hi":
        if user_number in user:
            user.pop(user_number)
        user[user_number] = {
                "step": "ask_name",
                "name": "",
                "requirement": ""
            }
        return send_reply("what is your name")

    if user_number in user:
        current_step = user[user_number]["step"]
        if current_step == "ask_name":
            user[user_number]["name"] = user_msg
            user[user_number]["step"] = "ask_requirement"
            return send_reply(f"thanks {user_msg}, what do you need?")

        if current_step == "ask_requirement":
            user[user_number]["requirement"] = user_msg
            user[user_number]["step"] = "confirm"
            return send_reply(f"confirm your request : {user[user_number]['requirement']} (yes/no)")

        if current_step == "confirm":
            if user_msg.lower() == "yes":
                name = user[user_number]["name"] 
                requirement = user[user_number]["requirement"]
                number = user_number
                with open("leads.csv","a",newline = "") as f:
                    writer = csv.writer(f)
                    writer.writerow([name,number,requirement])
                user.pop(user_number)
                return send_reply(f"thank you {name}! we will contact you")
            elif user_msg.lower() == "no":
                user[user_number]["step"] = "ask_requirement"
                return send_reply(f"Tell me your requirement again")
            
            else :
                return send_reply(f"please type yes or no")
        if user_msg.lower() in ["ok","okay"]:
            return send_reply("okay")

    response = response_llm(user_msg)
    return send_reply(response)
 