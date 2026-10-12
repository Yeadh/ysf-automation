import os
import json
import requests
from google import genai
from google.genai import types

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PAGE_ID = os.environ["FB_PAGE_ID"]
PAGE_TOKEN = os.environ["FB_PAGE_TOKEN"]
TOPIC = os.environ.get("TOPIC", "motivational quotes")
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")

client = genai.Client(api_key=GEMINI_KEY)


def make_text():
    prompt = (
        f"Topic: {TOPIC}. Create a fresh Facebook post. "
        "Return JSON with keys: "
        "caption (Bengali, 2-3 short lines, plus 2-3 hashtags) and "
        "image_prompt (English, detailed, visual description for an image generator)."
    )
    r = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(r.text)


def make_image(prompt):
    r = client.models.generate_content(model=IMAGE_MODEL, contents=prompt)
    for part in r.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data
    raise RuntimeError("Image generate hoyni")


def post_to_facebook(caption, image_bytes):
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    res = requests.post(
        url,
        data={"message": caption, "access_token": PAGE_TOKEN},
        files={"source": ("post.png", image_bytes, "image/png")},
        timeout=60,
    )
    res.raise_for_status()
    print("Posted:", res.json())


if __name__ == "__main__":
    data = make_text()
    print("Caption:", data["caption"])
    img = make_image(data["image_prompt"])
    post_to_facebook(data["caption"], img)
