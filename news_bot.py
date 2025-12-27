import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURACJA
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

KATEGORIE = {
    "GŁÓWNE WIADOMOŚCI": "https://www.espn.com/espn/rss/nba/news",
    "NAJNOWSZE Z PARKIETÓW": "https://www.cbssports.com/rss/headlines/nba/"
}

def generuj_po_polsku(tytul, opis):
    prompt = f"Jesteś dziennikarzem NBA. Napisz krótki wstęp (2 zdania) po polsku do artykułu: '{tytul}'. Użyj kontekstu: '{opis}'."
    try:
        response = model.generate_content(prompt)
        return response.text if len(response.text) > 10 else "Kliknij, aby poznać szczegóły tej sensacyjnej akcji w NBA."
    except:
        return "Zapraszamy do lektury pełnej relacji z ostatniego meczu."

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
    except: return "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"

def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    html_items = ""
    
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            
            html_items += f"<div class='section-header'>{nazwa}</div>"
            
            for news in feed.entries[:3]:
                img = pobierz_obrazek(news.link)
                opis_pl = generuj_po_polsku(news.title, getattr(news, 'description', ''))
                
                # LINKOWANIE: Każdy artykuł ma teraz przycisk 'CZYTAJ WIĘCEJ'
                html_items += f"""
                <div class='article-card'>
                    <img src='{img}' class='hero-img'>
                    <div class='info'>
                        <span class='category'>NBA TODAY</span>
                        <h2><a href='{news.link}' target='_blank'>{news.title}</a></h2>
                        <p>{opis_pl}</p>
                        <div class='footer-meta'>
                            <a href='{news.link}' target='_blank' class='read-btn'>CZYTAJ PEŁNY ARTYKUŁ →</a>
                            <button class='like-btn' onclick='this.classList.toggle("liked")'>❤️</button>
                        </div>
                    </div>
                </div>"""
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Roboto:wght@400;700&display=swap');
        body {{ background: #121212; color: #fff; font-family: 'Roboto', sans-serif; margin: 0; padding: 20px; }}
        .wrap {{ max-width: 900px; margin: auto; }}
        header {{ text-align: center; padding: 40px 0; background: linear-gradient(to bottom, #1d428a, #121212); border-radius: 15px; margin-bottom: 30px; }}
        h1 {{ font-family: 'Oswald', sans-serif; font-size: 4rem; margin: 0; color: #f58426; }}
        .section-header {{ font-family: 'Oswald', sans-serif; font-size: 1.5rem; color: #f58426; margin: 40px 0 20px 0; border-bottom: 2px solid #333; }}
        
        /* STYLIZACJA KARTY */
        .article-card {{ background: #1e1e1e; border-radius: 12px; overflow: hidden; margin-bottom: 30px; border: 1px solid #333; transition: 0.3s; }}
        .article-card:hover {{ transform: translateY(-5px); border-color: #f58426; }}
        .hero-img {{ width: 100%; height: 400px; object-fit: cover; }}
        .info {{ padding: 25px; }}
        h2 a {{ color: #fff; text-decoration: none; font-family: 'Oswald', sans-serif; font-size: 1.8rem; }}
        h2 a:hover {{ color: #f58426; }}
        p {{ color: #aaa; font-size: 1.1rem; line-height: 1.6; }}
        
        /* PRZYCISKI */
        .footer-meta {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }}
        .read-btn {{ background: #f58426; color: #000; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 0.9rem; }}
        .like-btn {{ background: #333; border: none; color: #fff; padding: 10px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; }}
        .like-btn.liked {{ background: #e0245e; }}
    </style></head>
    <body><div class='wrap'>
        <header><h1>NBA DAILY PL</h1><p>AKTUALIZACJA: {teraz}</p></header>
        {html_items}
    </div></body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(szablon)

if __name__ == "__main__": stworz_gazete()
