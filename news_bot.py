import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

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
    "ŚWIAT": "https://tvn24.pl/swiat.xml"
}

def wyczysc_html(tekst):
    # Usuwa tagi <img> z opisu, aby nie dublować zdjęć
    return re.sub(r'<img.*?>', '', tekst)

def generuj_artykul_ai(tytul, opis):
    opis_clean = wyczysc_html(opis)
    prompt = f"Napisz 3 krótkie zdania o: {tytul}. Fakty: {opis_clean}. Użyj tylko <p>."
    try:
        response = model.generate_content(prompt)
        if response.text and len(response.text) > 20:
            return response.text
        return f"<p>{opis_clean[:200]}...</p>"
    except:
        return f"<p>{opis_clean[:200]}...</p>"

def generuj_komentarze_ai(tytul):
    prompt = f"Napisz 3 krótkie, JEDNOZDANIOWE opinie fikcyjnych ludzi o tytule: {tytul}. 1.Janusz(fajnie), 2.Grażyna(narzeka), 3.Profesor(mądrze). Formatuj: <div class='comment'><b>Imię:</b> Treść</div>"
    try:
        response = model.generate_content(prompt)
        # Jeśli AI zablokuje, rzuć błąd do except
        if not response.text: raise Exception()
        return f"<div class='comments-section'><h4>Komentarze czytelników:</h4>{response.text}</div>"
    except:
        # Rezerwowe komentarze, gdy AI blokuje temat wojenny
        return f"""<div class='comments-section'><h4>Komentarze czytelników:</h4>
        <div class='comment'><b>Janusz:</b> Ważny temat, dobrze że o tym piszecie! 🧐</div>
        <div class='comment'><b>Grażyna:</b> Znowu takie wieści, strach włączać internet.</div>
        <div class='comment'><b>Profesor:</b> Sytuacja wymaga głębokiej analizy geopolitycznej.</div></div>"""

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
                tresc = generuj_artykul_ai(news.title, getattr(news, 'summary', ''))
                komentarze = generuj_komentarze_ai(news.title)
                img_tag = f"<img src='{img}' class='news-img'>" if img else ""
                html_items += f"<div class='news-card'><h2>{news.title}</h2>{img_tag}{tresc}{komentarze}</div>"
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; background: #1a1c2c; color: #eee; margin: 0; padding: 20px; }}
        .container {{ max-width: 700px; margin: auto; }}
        h1 {{ text-align: center; color: #4ecca3; font-size: 3rem; }}
        .category-header {{ background: #4ecca3; color: #1a1c2c; padding: 10px; border-radius: 5px; margin-top: 30px; font-weight: bold; }}
        .news-card {{ background: #232946; margin: 20px 0; padding: 20px; border-radius: 15px; border: 1px solid #4ecca3; }}
        .news-img {{ width: 100%; border-radius: 10px; margin: 15px 0; display: block; }}
        .comments-section {{ background: #1a1c2c; padding: 15px; border-radius: 10px; margin-top: 20px; }}
        .comment {{ font-size: 0.9rem; margin-bottom: 10px; color: #b8c1ec; border-bottom: 1px solid #232946; padding-bottom: 5px; }}
        .comment b {{ color: #4ecca3; }}
    </style></head>
    <body><div class="container"><h1>THE AI TIMES</h1><p style="text-align:center">Wydanie: {teraz}</p>{html_items}</div></body></html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":
    stworz_gazete()
