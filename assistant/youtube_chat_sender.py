import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import logging
import time

logging.basicConfig(level=logging.INFO)
logging.getLogger("hpack").setLevel(logging.WARNING)

def load_credentials(path="youtube_credentials.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_live_chat_id(video_id, credentials_dict):
    creds = Credentials.from_authorized_user_info(credentials_dict)
    youtube = build('youtube', 'v3', credentials=creds)
    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()
    return response["items"][0]["liveStreamingDetails"]["activeLiveChatId"]

def split_message(text, max_length=200):
    words = text.split()
    parts = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_length:
            parts.append(current)
            current = word
        else:
            if current:
                current += " "
            current += word
    if current:
        parts.append(current)
    return parts

def send_youtube_message(live_chat_id, text, credentials_dict):
    creds = Credentials.from_authorized_user_info(credentials_dict)
    youtube = build('youtube', 'v3', credentials=creds)
    try:
        response = youtube.liveChatMessages().insert(
            part='snippet',
            body={
                'snippet': {
                    'liveChatId': live_chat_id,
                    'type': 'textMessageEvent',
                    'textMessageDetails': {'messageText': text}
                }
            }
        ).execute()
        print(f"Сообщение '{text}' отправлено в чат! Ответ API: {response}")
    except Exception as e:
        print("Ошибка при отправке сообщения:", e)

def send_long_youtube_message(live_chat_id, text, credentials_dict, max_length=200):
    for part in split_message(text, max_length):
        send_youtube_message(live_chat_id, part, credentials_dict)
        time.sleep(1)  # чтобы не попасть под rate-limit

def send_message_by_video_id(video_id, text, credentials_path="youtube_credentials.json"):
    """
    Загружает credentials, получает live_chat_id по video_id и отправляет сообщение в чат.
    """
    credentials = load_credentials(credentials_path)
    live_chat_id = get_live_chat_id(video_id, credentials)
    send_long_youtube_message(live_chat_id, text, credentials) 