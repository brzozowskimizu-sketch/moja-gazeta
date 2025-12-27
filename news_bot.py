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

model = genai.GenerativeModel('gemini-1.5-flash')

# ŹRÓDŁA NBA (RSS z ESPN i CBS Sports)
KATEGORIE = {
    "NBA NEWS": "https://www.espn.com/espn/rss/nba/news",
    "NBA ANALYSIS": "https://www.cbssports.com/rss/headlines/nba/"
}

def wyczysc_html(tekst):
    return re.sub(r'<img.*?>', '', tekst)

def generuj_artykul_ai(tytul, opis):
    prompt = f"Jesteś ekspertem NBA. Napisz 3 ekscytujące zdania o: {tytul}. Kontekst: {opis}. Użyj <p>."
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else f"<p>{opis[:200]}</p>"
    except:
        return f"<p>{opis[:200]}</p>"

def generuj_komentarze_ai(tytul):
    prompt = f"""Wymyśl 3 krótkie komentarze fanów NBA do newsa: '{tytul}':
    1. Seba (fanatyk Lakers, dużo ognia 🔥)
    2. Ekspert (pisze o statystykach i taktyce)
    3. Hejter (narzeka, że kiedyś NBA była lepsza)
    Format: <div class='comment'><b>Imię:</b> Treść</div>"""
    try:
        response = model.generate_content(prompt)
        return f"<div class='comments-section'><h4>Dyskusja pod halą:</h4>{response.text}</div>"
    except:
        return ""

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1504450758481-7338eba7524a?w=800"
    except: return "https://images.unsplash.com/photo-1504450758481-7338eba7524a?w=800"

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
            for news in feed.entries[:3]:
                img = pobierz_obrazek(news.link)
                tresc = generuj_artykul_ai(news.title, getattr(news, 'summary', ''))
                komentarze = generuj_komentarze_ai(news.title)
                img_tag = f"<img src='{img}' class='news-img'>" if img else ""
                html_items += f"<div class='news-card'><h2>{news.title}</h2>{img_tag}{tresc}{komentarze}</div>"
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: 'Arial Black', sans-serif; background: #000; color: #fff; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: auto; }}
        h1 {{ text-align: center; color: #F58426; font-size: 4rem; text-transform: uppercase; border-bottom: 5px solid #1D428A; }}
        .category-header {{ background: #1D428A; color: #fff; padding: 10px; margin-top: 30px; border-radius: 5px; }}
        .news-card {{ background: #111; margin: 20px 0; padding: 25px; border-radius: 0; border-left: 10px solid #F58426; box-shadow: 5px 5px 0px #1D428A; }}
        .news-img {{ width: 100%; border: 2px solid #333; margin: 15px 0; }}
        h2 {{ color: #F58426; text-transform: uppercase; font-size: 1.5rem; }}
        p {{ color: #ccc; line-height: 1.6; }}
        .comments-section {{ background: #222; padding: 15px; margin-top: 20px; border-radius: 5px; }}
        .comment {{ font-size: 0.9rem; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; color: #aaa; }}
        .comment b {{ color: #F58426; }}
    </style></head>
    <body><div class="container"><h1>NBA DAILY</h1><p style="text-align:center">Aktualizacja: {teraz}</p>{html_items}</div></body></html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":
    stworz_gazete()
