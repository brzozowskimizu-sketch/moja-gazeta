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

# ŹRÓDŁA NBA (RSS)
KATEGORIE = {
    "WIADOMOŚCI NBA": "https://www.espn.com/espn/rss/nba/news",
    "ANALIZY I TRANSFERY": "https://www.cbssports.com/rss/headlines/nba/"
}

# 2. FUNKCJE GENERUJĄCE TREŚĆ PO POLSKU
def generuj_artykul_ai(tytul, opis):
    prompt = f"Jesteś polskim dziennikarzem sportowym. Przetłumacz i streść news: '{tytul}' na podstawie '{opis}'. Napisz 3 konkretne zdania po polsku. Użyj <p>."
    try:
        response = model.generate_content(prompt)
        if response.text and len(response.text) > 30:
            return response.text
        return f"<p>{tytul}. Przeczytaj więcej w pełnym artykule.</p>"
    except:
        return f"<p>Aktualnie brak szczegółowego opisu dla tego wydarzenia.</p>"

def generuj_komentarze_ai(tytul):
    prompt = f"""Wymyśl 3 krótkie komentarze polskich fanów NBA pod newsa: '{tytul}':
    1. Mirek (fan starej szkoły, narzeka na brak obrony)
    2. Młody (fan rzutów za 3, używa emotek)
    3. Ekspert (poważnie analizuje statystyki)
    Format: <div class='comment'><b>Imię:</b> Treść</div>"""
    try:
        response = model.generate_content(prompt)
        # Czyścimy ewentualny kod Markdown z odpowiedzi
        clean_text = response.text.replace('```html', '').replace('```', '')
        return f"<div class='comm-box'><h5>DYSKUSJA NA FORUM:</h5>{clean_text}</div>"
    except:
        # System awaryjny - polskie komentarze uniwersalne
        return f"""<div class='comm-box'><h5>DYSKUSJA NA FORUM:</h5>
        <div class='comment'><b>Mirek:</b> Kiedyś to by go tak do kosza nie dopuścili...</div>
        <div class='comment'><b>Młody:</b> Co za akcja! NBA to jest inna planeta! 🔥</div>
        <div class='comment'><b>Ekspert:</b> Kluczowy moment meczu, statystyki rzutowe to potwierdzają.</div></div>"""

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
    except: return "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"

# 3. BUDOWA STRONY HTML
def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    html_items = ""
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            
            html_items += f"<div class='cat-label'>{nazwa}</div>"
            
            for news in feed.entries[:3]:
                img = pobierz_obrazek(news.link)
                tresc = generuj_artykul_ai(news.title, getattr(news, 'description', ''))
                komentarze = generuj_komentarze_ai(news.title)
                
                html_items += f"""
                <div class='card'>
                    <h2>{news.title}</h2>
                    <img src='{img}' class='main-img'>
                    <div class='text'>{tresc}</div>
                    {komentarze}
                </div>"""
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NBA PO POLSKU</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Roboto:wght@300;400&display=swap');
        body {{ background: #0a0a0a; color: #fff; font-family: 'Roboto', sans-serif; margin: 0; padding: 20px; }}
        .wrap {{ max-width: 800px; margin: auto; }}
        header {{ text-align: center; padding: 40px 0; border-bottom: 3px solid #f58426; margin-bottom: 20px; }}
        h1 {{ font-family: 'Oswald', sans-serif; font-size: 4rem; color: #f58426; margin: 0; text-transform: uppercase; }}
        .cat-label {{ background: #1d428a; color: #fff; display: inline-block; padding: 8px 20px; font-family: 'Oswald', sans-serif; margin-top: 30px; border-radius: 4px; }}
        .card {{ background: #1a1a1a; margin: 25px 0; padding: 25px; border-radius: 12px; border: 1px solid #333; transition: 0.3s; }}
        .card:hover {{ border-color: #f58426; transform: translateY(-5px); }}
        .main-img {{ width: 100%; border-radius: 8px; margin: 15px 0; }}
        h2 {{ font-family: 'Oswald', sans-serif; color: #f58426; font-size: 1.8rem; margin: 0; }}
        .text {{ line-height: 1.6; font-size: 1.1rem; color: #ddd; }}
        .comm-box {{ background: #000; padding: 15px; border-radius: 8px; margin-top: 20px; border-top: 2px solid #1d428a; }}
        h5 {{ color: #1d428a; margin: 0 0 10px 0; letter-spacing: 1px; font-family: 'Oswald', sans-serif; }}
        .comment {{ font-size: 0.9rem; margin: 8px 0; color: #bbb; border-bottom: 1px solid #222; padding-bottom: 5px; }}
        .comment b {{ color: #f58426; }}
    </style></head>
    <body><div class='wrap'>
        <header><h1>NBA PO POLSKU</h1><p>NAJLEPSZA LIGA ŚWIATA W TWOIM JĘZYKU | {teraz}</p></header>
        {html_items}
    </div></body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":
    stworz_gazete()
