import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# POBIERANIE KLUCZA Z USTAWIEŃ GITHUBA
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)

# Tryb 1.5 Flash z WYŁĄCZONYMI filtrami dla dziennikarstwa
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
    prompt = f"Jesteś dziennikarzem. Napisz 3-zdaniowy raport newsowy o: {tytul}. Fakty: {opis}. Użyj formatu HTML <p>."
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "<p>Relacja w przygotowaniu...</p>"
    except: return "<p>Relacja w przygotowaniu...</p>"

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        return soup.find('meta', property='og:image')['content']
    except: return None

def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    html_items = ""
    
    for nazwa, url in KATEGORIE.items():
        feed = feedparser.parse(url)
        html_items += f"<div style='background:#1a73e8; color:white; padding:10px; margin-top:20px;'>{nazwa}</div>"
        for news in feed.entries[:2]:
            img = pobierz_obrazek(news.link)
            tresc = generuj_artykul_ai(news.title, getattr(news, 'summary', ''))
            img_tag = f"<img src='{img}' style='width:100%; border-radius:10px;'>" if img else ""
            html_items += f"<div style='margin-bottom:30px;'><h2>{news.title}</h2>{img_tag}{tresc}</div>"

    szablon = f"<html><body style='max-width:800px; margin:auto; font-family:sans-serif; padding:20px;'><h1>THE AI TIMES</h1><p>Aktualizacja: {teraz}</p>{html_items}</body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":

    stworz_gazete()
