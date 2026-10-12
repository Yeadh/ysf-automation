import os
import json
import time
import html
import base64
from string import Template

import requests
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

SITE_URL = "https://www.yasasmartfinances.site/"
BRAND = "Yasa Smart Finance"
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = "gemini-3-flash-preview"

# Proti ghontay ekta angle, jate post gulo repeat na hoy
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

# Card er rong: bg, heading gradient (g1 -> g2), button er rong
PALETTES = [
    {
        "bg": "radial-gradient(900px 600px at 100% 0%, rgba(20,150,150,.55), transparent 60%),"
              "radial-gradient(800px 600px at 100% 100%, rgba(180,70,80,.55), transparent 60%),"
              "linear-gradient(135deg,#1c2f80 0%,#1b1650 50%,#4a2fa8 100%)",
        "g1": "#ffc83d", "g2": "#ff5f7a", "cta": "#19c48f",
    },
    {
        "bg": "radial-gradient(900px 600px at 100% 0%, rgba(40,190,140,.45), transparent 60%),"
              "linear-gradient(135deg,#06322f 0%,#0b2740 55%,#18305f 100%)",
        "g1": "#7bf0c0", "g2": "#ffe27a", "cta": "#ffc83d",
    },
    {
        "bg": "radial-gradient(900px 600px at 0% 100%, rgba(255,140,60,.40), transparent 60%),"
              "linear-gradient(135deg,#101a45 0%,#1b2a78 55%,#2b1d6b 100%)",
        "g1": "#ffb44d", "g2": "#ff6a88", "cta": "#2fd3a0",
    },
    {
        "bg": "radial-gradient(900px 600px at 100% 100%, rgba(255,95,160,.40), transparent 60%),"
              "linear-gradient(135deg,#2a1260 0%,#1d1650 50%,#10285c 100%)",
        "g1": "#8fd3ff", "g2": "#d49bff", "cta": "#19c48f",
    },
]

DEFAULT_CARD = {
    "headline_top": "মাস শেষে টাকা",
    "headline_accent": "কোথায় যায়?",
    "subtitle": "বাংলায় পারিবারিক হিসাবের অ্যাপ",
    "bullets": ["আয়-ব্যয় ও বাজেট", "সঞ্চয়ের লক্ষ্য", "ঋণ ও ইএমআই", "বিল রিমাইন্ডার"],
    "badge": "বাজেটের মধ্যে আছেন",
    "balance": "৳ ৪৮,৫০০",
    "income": "৬৫,০০০",
    "expense": "১৬,৫০০",
    "saving": "১২,০০০",
    "bars": [55, 30, 70, 40, 95, 62],
    "cat1_name": "খাবার",
    "cat1_pct": 60,
    "cat2_name": "বিদ্যুৎ",
    "cat2_pct": 30,
    "cta": "এখনই ডাউনলোড করুন",
    "footer": "আপনার হিসাব থাকে আপনার ফোনেই",
}

CARD_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="bn"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1080px;font-family:"Hind Siliguri","Noto Sans Bengali","FreeSans",sans-serif}
.card{position:relative;width:1080px;height:1080px;overflow:hidden;background:${bg};color:#fff}
.abs{position:absolute}
.brand{left:60px;top:56px;display:flex;align-items:center;gap:26px}
.logo{width:110px;height:110px;border-radius:26px;overflow:hidden;display:block}
.brand-name{font-size:48px;font-weight:700;line-height:1.1}
.brand-sub{font-size:32px;color:#b9bfe8;line-height:1.2}
.h1{left:60px;top:190px;font-size:98px;font-weight:700;line-height:1.35;white-space:nowrap;display:inline-block}
.h2{left:60px;top:298px;font-size:98px;font-weight:700;line-height:1.45;white-space:nowrap;display:inline-block;
    padding-bottom:6px;background:linear-gradient(90deg,${g1},${g2});-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{left:60px;top:462px;font-size:32px;color:#b9bfe8;white-space:nowrap;display:inline-block}
.bul{left:60px;top:538px;width:600px}
.row{display:flex;align-items:center;gap:26px;height:84px}
.ic{width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex:none}
.rt{font-size:46px;font-weight:700;white-space:nowrap;display:inline-block}
.cta{left:60px;top:890px;width:500px;height:92px;border-radius:46px;background:${cta_color};color:#06231b;
     font-size:42px;font-weight:700;display:flex;align-items:center;justify-content:center;
     box-shadow:0 8px 0 rgba(0,0,0,.25)}
.cta span{display:inline-block;white-space:nowrap}
.foot{left:60px;top:1000px;font-size:28px;color:#c3c7ea;white-space:nowrap;display:inline-block}
.badge{left:650px;top:318px;height:56px;padding:0 26px;border:3px solid #19c48f;border-radius:30px;
       background:rgba(8,14,30,.85);font-size:26px;font-weight:700;display:flex;align-items:center}
.badge span{display:inline-block;white-space:nowrap}
.phone{left:690px;top:392px;width:310px;height:720px;border:8px solid #3a4766;border-radius:54px;
       background:#0c1220;padding:26px 22px}
.pl{font-size:22px;color:#8f9ab8;white-space:nowrap}
.bal{font-size:54px;font-weight:700;color:#19c48f;line-height:1.3;white-space:nowrap;margin-bottom:12px;display:inline-block}
.mini{display:flex;gap:8px}
.mc{flex:1;border:1px solid #1d273b;border-radius:12px;background:#0f1729;padding:8px 4px;text-align:center}
.ml{font-size:18px;color:#8f9ab8;line-height:1.3}
.mv{font-size:20px;font-weight:700;line-height:1.4;white-space:nowrap}
.bars{display:flex;align-items:flex-end;gap:12px;height:210px;margin:34px 0 22px 2px}
.bar{width:28px;border-radius:5px}
.pr{margin-top:10px;font-size:22px;color:#a9b3cf;line-height:1.4}
.tr{height:8px;border-radius:4px;background:#1c2536;margin-top:4px}
.fl{height:8px;border-radius:4px;background:#19c48f}
</style></head><body>
<div class="card">
  <div class="abs brand">${logo}<div><div class="brand-name">Yasa</div><div class="brand-sub">Smart Finance</div></div></div>
  <div class="abs h1 fit" data-max="960">${headline_top}</div>
  <div class="abs h2 fit" data-max="570">${headline_accent}</div>
  <div class="abs sub fit" data-max="600">${subtitle}</div>
  <div class="abs bul">${bullets}</div>
  <div class="abs cta"><span class="fit" data-max="440">${cta}</span></div>
  <div class="abs foot fit" data-max="600">${footer}</div>
  <div class="abs badge"><span class="fit" data-max="330">${badge}</span></div>
  <div class="abs phone">
    <div class="pl">মোট ব্যালেন্স</div>
    <div class="bal fit" data-max="250">${balance}</div>
    <div class="mini">
      <div class="mc"><div class="ml">আয়</div><div class="mv" style="color:#19c48f">${income}</div></div>
      <div class="mc"><div class="ml">ব্যয়</div><div class="mv" style="color:#ff6b86">${expense}</div></div>
      <div class="mc"><div class="ml">সঞ্চয়</div><div class="mv" style="color:#6ea8ff">${saving}</div></div>
    </div>
    <div class="bars">${bars}</div>
    <div class="pr">${cat1_name}<div class="tr"><div class="fl" style="width:${cat1_pct}%"></div></div></div>
    <div class="pr">${cat2_name}<div class="tr"><div class="fl" style="width:${cat2_pct}%"></div></div></div>
  </div>
</div>
</body></html>
""")

FIT_JS = """
() => {
  document.querySelectorAll('.fit').forEach(el => {
    const max = parseFloat(el.dataset.max);
    let size = parseFloat(getComputedStyle(el).fontSize);
    while (el.getBoundingClientRect().width > max && size > 18) {
      size -= 2;
      el.style.fontSize = size + 'px';
    }
  });
}
"""

CHECK_COLORS = ["#5aa2ff", "#19d39a", "#ffa24d", "#ff6b8a"]
CHECK_SVG = (
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#0c1220" '
    'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 12.5l4.5 4.5L19 7"/></svg>'
)
LOGO_SVG = (
    '<svg class="logo" viewBox="0 0 100 100"><rect width="100" height="100" rx="24" fill="#141a3a"/>'
    '<g fill="none" stroke-width="9" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M30 28L50 55" stroke="#6aa7ff"/><path d="M50 55L72 25" stroke="#ff9b4a"/>'
    '<path d="M60 24H74V38" stroke="#ff9b4a"/><path d="M50 55V78" stroke="#19d3a2"/></g></svg>'
)

client = None


def esc(value):
    return html.escape(str(value))


def generate_with_retry(prompt, config=None):
    models = [TEXT_MODEL, FALLBACK_MODEL]
    last = None
    for model in models:
        for attempt in range(3):
            try:
                return client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
            except Exception as e:
                last = e
                print(f"{model} attempt {attempt + 1} failed: {e}")
                time.sleep(5 * (attempt + 1))
    raise last


def make_text():
    angle = ANGLES[int(time.time() // 3600) % len(ANGLES)]
    prompt = (
        f"Brand: {BRAND}, ekta Bangla family finance app "
        "(ay-bay, budget, shonchoy, EMI, bill reminder, offline, PIN/fingerprint lock, bigyapon-mukto). "
        f"Aj-ker angle: {angle}. "
        "Create a fresh Facebook post for Bangladeshi families. "
        "Return ONLY JSON with these keys, all text in Bengali script and all numbers in Bengali digits: "
        f"caption (3-4 short lines, friendly tone, 1-2 emoji, ends with 'ডাউনলোড: {SITE_URL}' and 2-3 hashtags); "
        "headline_top (max 14 characters, first line of a catchy headline, e.g. a question start); "
        "headline_accent (max 12 characters, second line, ends the headline); "
        "subtitle (max 30 characters); "
        "bullets (exactly 4 feature phrases, each max 16 characters, matching the angle); "
        "badge (max 20 characters, short status like 'বাজেটের মধ্যে আছেন'); "
        "balance (like '৳ ৪৮,৫০০'); income, expense, saving (Bengali-digit amounts with commas, no currency sign); "
        "bars (6 integers between 25 and 100); "
        "cat1_name, cat2_name (expense category names, max 8 characters); "
        "cat1_pct, cat2_pct (integers between 15 and 90); "
        "cta (max 20 characters, a download call to action); "
        "footer (max 36 characters, a trust line)."
    )
    r = generate_with_retry(
        prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(r.text)


def clean_card(data):
    card = dict(DEFAULT_CARD)
    for key in card:
        if key in data and data[key]:
            card[key] = data[key]
    bullets = card["bullets"]
    if not isinstance(bullets, list) or len(bullets) < 4:
        bullets = DEFAULT_CARD["bullets"]
    card["bullets"] = [str(b) for b in bullets[:4]]
    try:
        bars = [max(20, min(100, int(b))) for b in card["bars"]][:6]
    except Exception:
        bars = DEFAULT_CARD["bars"]
    if len(bars) < 6:
        bars = DEFAULT_CARD["bars"]
    card["bars"] = bars
    for key in ("cat1_pct", "cat2_pct"):
        try:
            card[key] = max(10, min(95, int(card[key])))
        except Exception:
            card[key] = DEFAULT_CARD[key]
    return card


def build_html(card, palette):
    bullets_html = "".join(
        f'<div class="row"><div class="ic" style="background:{CHECK_COLORS[i]}">{CHECK_SVG}</div>'
        f'<div class="rt fit" data-max="500">{esc(text)}</div></div>'
        for i, text in enumerate(card["bullets"])
    )
    bars_html = "".join(
        f'<div class="bar" style="height:{pct * 2}px;'
        f'background:{"#19c48f" if i % 2 == 0 else "#ff5f7a"}"></div>'
        for i, pct in enumerate(card["bars"])
    )
    logo_html = LOGO_SVG
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img class="logo" src="data:image/png;base64,{b64}">'
    values = {k: esc(v) for k, v in card.items() if k not in ("bullets", "bars")}
    return CARD_TEMPLATE.substitute(
        values,
        bg=palette["bg"],
        g1=palette["g1"],
        g2=palette["g2"],
        cta_color=palette["cta"],
        logo=logo_html,
        bullets=bullets_html,
        bars=bars_html,
    )


def render_card(page_html):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        try:
            page.set_content(page_html, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print("Font load slow, local font diye cholchi:", e)
        page.evaluate("document.fonts.ready")
        page.evaluate(FIT_JS)
        png = page.screenshot(type="png")
        browser.close()
    return png


def post_to_facebook(caption, image_bytes):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_TOKEN"]
    url = f"https://graph.facebook.com/v21.0/{page_id}/photos"
    res = requests.post(
        url,
        data={"message": caption, "access_token": token},
        files={"source": ("post.png", image_bytes, "image/png")},
        timeout=60,
    )
    if not res.ok:
        print("Image size:", len(image_bytes), "bytes")
        print("Facebook error:", res.status_code, res.text)
        res.raise_for_status()
    print("Posted:", res.json())


if __name__ == "__main__":
    hour = int(time.time() // 3600)
    palette = PALETTES[hour % len(PALETTES)]

    if os.environ.get("PREVIEW") == "1":
        png = render_card(build_html(clean_card({}), palette))
        with open("preview.png", "wb") as f:
            f.write(png)
        print("preview.png saved")
    else:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        data = make_text()
        print("Caption:", data.get("caption"))
        card = clean_card(data)
        png = render_card(build_html(card, palette))
        post_to_facebook(data["caption"], png)
