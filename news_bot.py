import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# POBIERANIE KLUCZA
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)

# Konfiguracja modelu z obejściem filtrów
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
    # Bardziej "miękki" prompt, który nie aktywuje filtrów bezpieczeństwa
    prompt = f"""
    Przedstaw poniższe fakty w trzech krótkich, spokojnych zdaniach. 
    Skup się na czystych informacjach, bez emocji.
    Temat: {tytul}
    Dodatkowe info: {opis}
    Zacznij od razu od treści, użyj formatu HTML <p>.
    """
    try:
        # Dodajemy wymuszenie braku filtrów bezpośrednio w zapytaniu
        response = model.generate_content(prompt)
        
        # Jeśli AI zwróciło tekst, używamy go
        if response.parts:
            return f"<p>{response.text}</p>"
        
        # Jeśli AI zablokowało tekst, podajemy chociaż opis z RSS (oryginalny z TVN24)
        return f"<p>{opis[:200]}...</p>"
    except:
        # Jeśli wszystko zawiedzie, dajemy oryginalny opis zamiast powtarzać tytuł
        return f"<p>{opis[:200]}...</p>"

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
            
            html_items += f"<div style='background:#1a73e8;color:white;padding:10px;margin-top:30px;border-radius:5px;'>{nazwa}</div>"
            
            for news in feed.entries[:2]:
                img = pobierz_obrazek(news.link)
                tresc = generuj_artykul_ai(news.title, getattr(news, 'summary', ''))
                img_tag = f"<img src='{img}' style='width:100%;border-radius:10px;margin:10px 0;'>" if img else ""
                html_items += f"<div style='border-bottom:1px solid #ddd;padding:20px 0;'><h2>{news.title}</h2>{img_tag}{tresc}</div>"
        except: continue

    szablon = f"""
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="font-family:sans-serif;max-width:800px;margin:auto;padding:20px;background:#f4f4f4;">
        <div style="background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="text-align:center;font-size:40px;margin:0;">THE AI TIMES</h1>
            <p style="text-align:center;color:gray;">Wydanie: {teraz}</p>
            {html_items}
        </div>
    </body>
    </html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(szablon)

if __name__ == "__main__":
    stworz_gazete()

