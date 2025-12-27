import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# 1. KONFIGURACJA AI
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

KATEGORIE = {
    "NBA POLSKA - NAJNOWSZE": "https://www.espn.com/espn/rss/nba/news",
    "ANALIZY EKSPERCKIE": "https://www.cbssports.com/rss/headlines/nba/"
}

# 2. GENEROWANIE TREŚCI PO POLSKU
def generuj_artykul_ai(tytul, opis):
    prompt = f"Jesteś polskim ekspertem NBA. Przetłumacz i streść news: '{tytul}' na podstawie '{opis}'. Napisz 3 konkretne zdania po polsku. Użyj <p>."
    try:
        response = model.generate_content(prompt)
        return response.text if len(response.text) > 20 else f"<p>{tytul}</p>"
    except: return f"<p>{tytul}</p>"

def generuj_komentarze_ai(tytul):
    prompt = f"Wymyśl 3 krótkie opinie polskich fanów NBA o: '{tytul}'. 1.Mirek, 2.Młody, 3.Ekspert. Formatuj: <div class='comment'><b>Imię:</b> Treść</div>"
    try:
        response = model.generate_content(prompt)
        # Wymuszamy wyświetlenie, nawet jeśli AI zwróci pusty tekst
        content = response.text if response.text else "Brak nowych komentarzy."
        return f"<div class='comm-box'><h5>DYSKUSJA FANÓW:</h5>{content}</div>"
    except:
        return f"<div class='comm-box'><h5>DYSKUSJA FANÓW:</h5><div class='comment'><b>Mirek:</b> Solidne info!</div></div>"

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
    except: return "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"

# 3. BUDOWA STRONY (INSPIRACJA TWOIM PSD)
def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    html_items = ""
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            html_items += f"<div class='section-title'>{nazwa}</div>"
            for news in feed.entries[:3]:
                img = pobierz_obrazek(news.link)
                tresc = generuj_artykul_ai(news.title, getattr(news, 'description', ''))
                komentarze = generuj_komentarze_ai(news.title)
                html_items += f"""
                <div class='card'>
                    <div class='card-header'>NEWS</div>
                    <h2>{news.title}</h2>
                    <img src='{img}' class='img'>
                    <div class='content'>{tresc}</div>
                    {komentarze}
                </div>"""
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body {{ background: #121212; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: auto; }}
        header {{ background: #1a1a1a; padding: 30px; border-radius: 15px; border-bottom: 4px solid #f58426; text-align: center; margin-bottom: 40px; }}
        h1 {{ font-weight: 900; font-size: 3.5rem; color: #fff; margin: 0; letter-spacing: -2px; }}
        h1 span {{ color: #f58426; }}
        .section-title {{ font-size: 1.2rem; font-weight: bold; color: #f58426; text-transform: uppercase; margin: 40px 0 20px 0; border-left: 5px solid #1d428a; padding-left: 15px; }}
        .card {{ background: #1e1e1e; border-radius: 12px; padding: 25px; margin-bottom: 30px; border: 1px solid #333; }}
        .card-header {{ font-size: 0.7rem; font-weight: bold; color: #f58426; border: 1px dashed #f58426; display: inline-block; padding: 2px 8px; margin-bottom: 15px; }}
        h2 {{ font-size: 1.6rem; margin: 0 0 15px 0; line-height: 1.2; }}
        .img {{ width: 100%; border-radius: 8px; filter: brightness(0.9); }}
        .content {{ color: #bbb; line-height: 1.6; margin: 20px 0; font-size: 1.05rem; }}
        .comm-box {{ background: #141414; padding: 20px; border-radius: 10px; border-left: 4px solid #1d428a; }}
        .comm-box h5 {{ margin: 0 0 10px 0; font-size: 0.8rem; color: #1d428a; text-transform: uppercase; }}
        .comment {{ font-size: 0.9rem; color: #999; margin-bottom: 8px; border-bottom: 1px solid #222; padding-bottom: 5px; }}
        .comment b {{ color: #f58426; }}
    </style></head>
    <body><div class='container'>
        <header><h1>NBA<span>DZISIAJ</span></h1><p>POLSKA EDYCJA | {teraz}</p></header>
        {html_items}
    </div></body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(szablon)

if __name__ == "__main__": stworz_gazete()
