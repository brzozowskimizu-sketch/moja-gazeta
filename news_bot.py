import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# KONFIGURACJA
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash',
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
    ])

KATEGORIE = {
    "POLSKA": "https://tvn24.pl/polska.xml",
    "ŚWIAT": "https://tvn24.pl/swiat.xml",
    "BIZNES": "https://tvn24.pl/biznes.xml"
}

def generuj_artykul_ai(tytul, opis):
    prompt = f"Jesteś dziennikarzem. Napisz 3 ciekawe zdania o: {tytul}. Fakty: {opis}. Użyj <p>."
    try:
        response = model.generate_content(prompt)
        # Sprawdzamy, czy AI faktycznie coś napisało, a nie tylko powtórzyło tytuł
        if response.text and len(response.text) > len(tytul) + 10:
            return response.text
        return f"<p>{opis[:250]}...</p>" # Jeśli AI zawiedzie, bierzemy opis z RSS
    except:
        return f"<p>{opis[:250]}...</p>"

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else ""
    except: return ""

def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    html_items = ""
    
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            
            html_items += f"<div class='category-header'>{nazwa}</div>"
            
            for news in feed.entries[:2]:
                img = pobierz_obrazek(news.link)
                # Pobieramy opis z RSS, żeby mieć co pokazać, gdy AI zablokuje treść
                raw_summary = getattr(news, 'summary', '')
                tresc = generuj_artykul_ai(news.title, raw_summary)
                
                img_tag = f"<img src='{img}' class='news-img'>" if img else ""
                html_items += f"<div class='news-card'><h2>{news.title}</h2>{img_tag}{tresc}</div>"
        except: continue

    szablon = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; }}
            h1 {{ text-align: center; font-size: 3rem; color: #38bdf8; margin-bottom: 5px; }}
            .date {{ text-align: center; color: #94a3b8; margin-bottom: 40px; }}
            .category-header {{ background: #1e293b; padding: 10px 20px; border-radius: 8px; font-weight: bold; color: #38bdf8; margin-top: 40px; border-left: 5px solid #38bdf8; }}
            .news-card {{ background: #1e293b; margin: 20px 0; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            .news-img {{ width: 100%; border-radius: 10px; margin: 15px 0; border: 1px solid #334155; }}
            h2 {{ font-size: 1.5rem; margin-top: 0; line-height: 1.3; color: #f1f5f9; }}
            p {{ color: #cbd5e1; line-height: 1.6; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>THE AI TIMES</h1>
            <p class="date">Wydanie Inteligentne: {teraz}</p>
            {html_items}
        </div>
    </body>
    </html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":
    stworz_gazete()
