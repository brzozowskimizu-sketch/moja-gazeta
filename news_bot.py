import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURACJA AI - WYŁĄCZENIE FILTRÓW
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
    "WYRÓŻNIONE": "https://www.espn.com/espn/rss/nba/news",
    "TABELA I ANALIZY": "https://www.cbssports.com/rss/headlines/nba/"
}

def generuj_po_polsku(tytul, opis):
    # Bardzo surowy prompt, żeby AI nie mogło "uciec" w angielski
    prompt = f"ZAKAZ ANGIELSKIEGO. Napisz po polsku 2 zdania o: {tytul}. Kontekst: {opis}. Tylko czysty tekst."
    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "Nowe wydarzenia w NBA. Sprawdź szczegóły akcji."
    except:
        return "Aktualizacja z parkietów NBA. Kliknij po więcej informacji."

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
    except: return "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"

def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    main_news = ""
    side_news = ""
    
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            
            for i, news in enumerate(feed.entries[:3]):
                img = pobierz_obrazek(news.link)
                opis_pl = generuj_po_polsku(news.title, getattr(news, 'description', ''))
                
                # Główna kolumna (lewa)
                if i == 0:
                    main_news += f"""
                    <div class='main-card'>
                        <div class='tag'>NEWS</div>
                        <img src='{img}'>
                        <h2>{news.title}</h2>
                        <p>{opis_pl}</p>
                        <div class='comments'>
                            <b>Mirek:</b> Solidne info! | <b>Młody:</b> 🔥 GOAT!
                        </div>
                    </div>"""
                else:
                    # Boczna kolumna (prawa)
                    side_news += f"""
                    <div class='side-item'>
                        <img src='{img}'>
                        <div>
                            <h4>{news.title}</h4>
                            <span>{teraz}</span>
                        </div>
                    </div>"""
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body {{ background: #1a1a1a; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 20px; }}
        .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; max-width: 1200px; margin: auto; }}
        header {{ text-align: left; padding: 20px 0; border-bottom: 1px solid #333; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ font-weight: 900; font-size: 2.5rem; text-transform: uppercase; margin: 0; }}
        h1 span {{ color: #f58426; }}
        .main-card {{ background: #252525; padding: 20px; border-radius: 4px; position: relative; }}
        .main-card img {{ width: 100%; border-radius: 4px; margin: 15px 0; }}
        .tag {{ position: absolute; top: 35px; left: 35px; background: #f58426; color: #000; font-size: 0.7rem; font-weight: bold; padding: 2px 10px; }}
        .side-panel {{ background: #252525; padding: 20px; border-radius: 4px; }}
        .side-item {{ display: flex; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 15px; }}
        .side-item img {{ width: 80px; height: 60px; object-fit: cover; border-radius: 4px; }}
        .side-item h4 {{ margin: 0; font-size: 0.9rem; line-height: 1.2; }}
        .comments {{ margin-top: 20px; font-size: 0.8rem; color: #f58426; border-top: 1px solid #333; padding-top: 10px; }}
        h2 {{ font-size: 2rem; margin: 10px 0; }}
        p {{ color: #aaa; line-height: 1.6; }}
    </style></head>
    <body>
        <div class='container'>
            <header><h1>NBA <span>TODAY</span></h1><div>{teraz}</div></header>
            <div class='grid'>
                <div class='left-col'>{main_news}</div>
                <div class='side-panel'><h3>LIVE SCORES</h3>{side_news}</div>
            </div>
        </div>
    </body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(szablon)

if __name__ == "__main__": stworz_gazete()
