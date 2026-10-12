import os
import json
import datetime
import requests
import urllib.parse
from google import genai
from google.genai import types

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
PAGE_ID = os.environ["FB_PAGE_ID"]
PAGE_TOKEN = os.environ["FB_PAGE_TOKEN"]
SITE_URL = "https://www.yasasmartfinances.site/"
BRAND = "Yasa Smart Finance"

# Proti din ekta angle (din onujayi ghurbe), jate post gulo repeat na hoy
ANGLES = [
    "ayo-bayer hishab roj likhe rakhar upokarita",
    "masik budget banano ar sima chharale sotorkota pawa",
    "shonchoy lokkho (emergency fund, laptop) dhape dhape joma",
    "EMI o rin er kisti hishab rakha, koto baki koto shodh",
    "bill reminder, deri hole jorimana ar tension theke mukti",
    "bank, bKash, Nagad ar cash alada hishab rakha",
    "poribarer sodossoder khoroch alada dekha",
    "dhar-den khata: kake dilen, kar kache pabe",
    "internet chhara offline hishab, PIN ar fingerprint lock e nirapotta",
    "bigyapon-mukto, shompurno Bangla app",
]
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-3.8-flash")

client = genai.Client(api_key=GEMINI_KEY)


def make_text():
    angle = ANGLES[datetime.date.today().toordinal() % len(ANGLES)]
    prompt = (
        f"Brand: {BRAND}, ekta Bangla family finance app "
        "(ay-bay, budget, shonchoy, EMI, bill reminder, offline, PIN/fingerprint lock, bigyapon-mukto). "
        f"Aj-ker angle: {angle}. "
        "Create a fresh Facebook post for Bangladeshi families. "
        "Return JSON with keys: "
        "caption (Bengali script, 3-4 short lines, friendly tone, 1-2 emoji, "
        f"ends with 'ডাউনলোড: {SITE_URL}' and 2-3 hashtags) and "
        "image_prompt (English; warm, modern illustration of a Bangladeshi family managing money "
        "relevant to the angle; absolutely NO text, letters or numbers in the image)."
    )
    r = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(r.text)


def make_image(prompt):
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + "?width=1024&height=1024&nologo=true"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    if "image" not in r.headers.get("content-type", ""):
        raise RuntimeError("Image paoa jayni")
    return r.content


def post_to_facebook(caption, image_bytes):
    url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"
    res = requests.post(
        url,
        data={"message": caption, "access_token": PAGE_TOKEN},
        files={"source": ("post.jpg", image_bytes, "image/jpeg")},
        timeout=60,
    )
    res.raise_for_status()
    print("Posted:", res.json())


if __name__ == "__main__":
    data = make_text()
    print("Caption:", data["caption"])
    img = make_image(data["image_prompt"])
    post_to_facebook(data["caption"], img)
