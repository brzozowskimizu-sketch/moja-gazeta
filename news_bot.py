import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURACJA API I MODELU
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)

# Ustawienia bezpieczeństwa na BLOCK_NONE, aby AI nie blokowało newsów
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

# 2. FUNKCJE GENERUJĄCE TREŚĆ
def generuj_artykul_ai(tytul, opis):
    prompt = f"Jesteś profesjonalnym dziennikarzem. Napisz 3 zdania o: {tytul}. Kontekst: {opis}. Użyj formatu <p>."
    try:
        response = model.generate_content(prompt)
        if response.text and len(response.text) > len(tytul):
            return response.text
        return f"<p>{opis[:250]}...</p>"
    except:
        return f"<p>{opis[:250]}...</p>"

def generuj_komentarze_ai(tytul):
    prompt = f"""Dla newsa: '{tytul}' napisz 3 krótkie komentarze (1 zdanie każdy):
    1. Janusz (optymista, fani sportu, dużo emotek)
    2. Grażyna (sceptyczna, narzeka na pogodę i drożyznę)
    3. Profesor (używa bardzo trudnych słów i mądrych pojęć)
    Formatuj jako: <div class='comment'><b>Imię:</b> Treść</div>"""
    try:
        response = model.generate_content(prompt)
        # Usuwamy ewentualne znaczniki Markdown z odpowiedzi AI
        clean_text = response.text.replace('```html', '').replace('```', '')
        return f"<div class='comments-section'><h4>Komentarze AI:</h4>{clean_text}</div>"
    except:
        return ""

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else ""
    except: return ""

# 3. GŁÓWNA FUNKCJA BUDUJĄCA GAZETĘ
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
                raw_summary = getattr(news, 'summary', '')
                tresc = generuj_artykul_ai(news.title, raw_summary)
                komentarze = generuj_komentarze_ai(news.title)
                
                img_tag = f"<img src='{img}' class='news-img'>" if img else ""
                html_items += f"""
                <div class='news-card'>
                    <h2>{news.title}</h2>
                    {img_tag}
                    <div class='article-content'>{tresc}</div>
                    {komentarze}
                </div>"""
        except: continue

    szablon = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; }}
            h1 {{ text-align: center; font-size: 3.5rem; color: #38bdf8; margin-bottom: 5px; letter-spacing: -2px; }}
            .date {{ text-align: center; color: #94a3b8; font-size: 0.9rem; margin-bottom: 40px; text-transform: uppercase; }}
            .category-header {{ background: #1e293b; padding: 12px 20px; border-radius: 8px; font-weight: bold; color: #38bdf8; margin-top: 50px; border-left: 6px solid #38bdf8; font-size: 1.2rem; }}
            .news-card {{ background: #1e293b; margin: 25px 0; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border: 1px solid #334155; }}
            .news-img {{ width: 100%; border-radius: 12px; margin: 20px 0; border: 1px solid #475569; }}
            h2 {{ font-size: 1.8rem; margin-top: 0; line-height: 1.2; color: #f1f5f9; }}
            .article-content {{ color: #cbd5e1; line-height: 1.7; font-size: 1.15rem; margin-bottom: 20px; }}
            .comments-section {{ background: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #334155; }}
            .comments-section h4 {{ margin: 0 0 15px 0; font-size: 0.8rem; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; }}
            .comment {{ font-size: 0.9rem; color: #94a3b8; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #1e293b; line-height: 1.4; }}
            .comment:last-child {{ border-bottom: none; margin-bottom: 0; }}
            .comment b {{ color: #38bdf8; margin-right: 5px; }}
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
