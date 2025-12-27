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

# --- NOWA KONFIGURACJA OMIJAJĄCA BLOKADY ---
# Ustawiamy wszystkie filtry na BLOCK_NONE
safety_config = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=safety_config
)

def generuj_artykul_ai(tytul, opis):
    # Dodajemy instrukcję bezpieczeństwa do samego promptu
    prompt = f"""
    Jesteś profesjonalnym, obiektywnym dziennikarzem. 
    Napisz krótką relację (3 zdania) na podstawie faktów: {tytul}. 
    Opis pomocniczy: {opis}.
    UWAGA: To są oficjalne wiadomości ze świata, opisz je bez oceniania.
    Używaj formatu HTML <p>.
    """
    try:
        response = model.generate_content(prompt)
        # Sprawdzamy czy AI nie zwróciło pustki przez filtry
        if response.candidates and response.candidates[0].content.parts:
            return response.text
        return f"<p>AI uznało ten temat za zbyt wrażliwy, ale tytuł to: <strong>{tytul}</strong></p>"
    except Exception as e:
        return f"<p>Błąd systemu: {tytul}</p>"

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

