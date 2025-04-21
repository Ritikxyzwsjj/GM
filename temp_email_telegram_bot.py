
import requests
import time
import random
import string
import re

# === CONFIGURE YOUR TELEGRAM CREDENTIALS ===
TELEGRAM_BOT_TOKEN = "7647515503:AAGS7t15F-BC-JewX6EcnpuBK2z-YOYGwP8"
TELEGRAM_CHAT_ID = "6437994839"

# === MAIL.TM TEMP EMAIL SETUP ===
domain_resp = requests.get("https://api.mail.tm/domains")
domain = domain_resp.json()["hydra:member"][0]["domain"]

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

username = random_string()
password = random_string()
email = f"{username}@{domain}"

account_payload = {"address": email, "password": password}
acc_resp = requests.post("https://api.mail.tm/accounts", json=account_payload)

if acc_resp.status_code != 201:
    print("Account creation failed:", acc_resp.text)
    exit()

token_resp = requests.post("https://api.mail.tm/token", json=account_payload)
token = token_resp.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"\nTemporary Email Created: {email}\nWaiting for OTP/email...\n")

# === NOTIFY VIA TELEGRAM EMAIL CREATED ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=data)

send_telegram(f"Temporary Email Created: {email}")

# === CHECK INBOX & FORWARD OTP ===
while True:
    inbox_resp = requests.get("https://api.mail.tm/messages", headers=headers)
    inbox = inbox_resp.json()

    if inbox["hydra:member"]:
        msg_id = inbox["hydra:member"][0]["id"]
        msg_resp = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
        content = msg_resp.json()
        
        sender = content['from']['address']
        subject = content['subject']
        text = content['text']

        print(f"\nFrom: {sender}\nSubject: {subject}\n\n{text}")
        
        # === Extract 6-digit OTP (if any) ===
        otp_match = re.search(r"\b\d{6}\b", text)
        otp = otp_match.group() if otp_match else "No OTP Found"

        # === Check if from Gmail or Google ===
        if "google" in sender.lower() or "gmail" in sender.lower() or "verification" in subject.lower():
            tag = "[GMAIL VERIFICATION]"
        else:
            tag = "[MESSAGE]"

        # === Send formatted message to Telegram ===
        tg_msg = f"{tag}\nFrom: {sender}\nSubject: {subject}\nOTP: {otp}\n\n{text}"
        send_telegram(tg_msg)
        break
    else:
        print("No messages yet. Checking again in 5 seconds...")
        time.sleep(5)
