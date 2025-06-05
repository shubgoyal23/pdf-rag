from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import atexit

from helpers.mongo_connect import mongo_create_one

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_PASS = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Create and store the global connection
smtp_server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
smtp_server.login(EMAIL_USER, EMAIL_PASS)

# Ensure it's closed properly when the app exits
atexit.register(lambda: smtp_server.quit())  

def reconnect_smtp():
    global smtp_server
    try:
        smtp_server.quit()
    except:
        pass
    smtp_server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
    smtp_server.login(EMAIL_USER, EMAIL_PASS)

file = open("email_template.txt", "r")
template = file.read()
file.close()

def send_email(data):
    to = data.get("to")
    subject = data.get("subject")
    body = data.get("body").replace("\n", "<br />")
    body = template.replace("###Subject###", subject).replace("###Body###", body)
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    mongo_create_one({"to": to, "subject": subject, "body": body, "created_at": datetime.now()}, "emails")
    try:
        smtp_server.send_message(msg)
        return True
    except Exception as e:
        reconnect_smtp()
        try:
            smtp_server.send_message(msg)
            return True
        except Exception as e2:
            return False
