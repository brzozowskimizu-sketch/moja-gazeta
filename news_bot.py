import feedparser
import google.generativeai as genai
import os
import urllib.request
import ssl
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. KONFIGURACJA AI
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

KATEGORIE = {
    "WYRÓŻNIONE": "https://www.espn.com/espn/rss/nba/news",
    "ANALIZY": "https://www.cbssports.com/rss/headlines/nba/"
}

WYNIKI = [
    {"home": "Lakers", "away": "Warriors", "score": "118 - 114", "status": "KONIEC"},
    {"home": "Celtics", "away": "76ers", "score": "102 - 140", "status": "KONIEC"},
    {"home": "Suns", "away": "Mavericks", "score": "88 - 92", "status": "III KWARTA"},
    {"home": "Bucks", "away": "Nets", "score": "105 - 111", "status": "KONIEC"}
]

def generuj_po_polsku(tytul, opis):
    prompt = f"Jesteś polskim ekspertem NBA. Przetłumacz i streść news: '{tytul}' na podstawie '{opis}'. Napisz dokładnie 2 zdania po polsku."
    try:
        response = model.generate_content(prompt)
        return response.text if len(response.text) > 10 else "Zapraszamy do lektury pełnej relacji z parkietów NBA."
    except: return "Aktualne informacje z USA. Kliknij poniżej, aby czytać dalej."

def pobierz_obrazek(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.content, 'html.parser')
        img = soup.find('meta', property='og:image')
        return img['content'] if img else "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"
    except: return "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"

def stworz_gazete():
    teraz = datetime.now().strftime("%d.%m.%Y | %H:%M")
    
    # HTML Wyników
    scores_html = "".join([f"""
        <div class='score-box'>
            <div class='score-teams'>{w['away']} @ {w['home']}</div>
            <div class='score-value'>{w['score']}</div>
            <div class='score-status'>{w['status']}</div>
        </div>
    """ for w in WYNIKI])

    # HTML Newsów
    news_html = ""
    for nazwa, url in KATEGORIE.items():
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
            
            section_id = nazwa.lower().replace("ó", "o")
            news_html += f"<div id='{section_id}' class='section-title'>{nazwa}</div>"
            
            for i, news in enumerate(feed.entries[:3]):
                img = pobierz_obrazek(news.link)
                opis_pl = generuj_po_polsku(news.title, getattr(news, 'description', ''))
                post_id = f"post-{section_id}-{i}"
                
                news_html += f"""
                <div class='card'>
                    <div class='tag'>LIVE</div>
                    <img src='{img}'>
                    <div class='card-body'>
                        <h2>{news.title}</h2>
                        <p>{opis_pl}</p>
                        
                        <div class='comment-section'>
                            <div id='list-{post_id}' class='comment-list'>
                                <div class='comment'><b>NBA_Bot:</b> Co sądzisz o tym transferze?</div>
                            </div>
                            <div class='comment-input-area'>
                                <input type='text' id='input-{post_id}' placeholder='Napisz coś...'>
                                <button onclick="addComment('{post_id}')">DODAJ</button>
                            </div>
                        </div>

                        <div class='card-footer'>
                            <a href='{news.link}' target='_blank' class='btn'>CZYTAJ WIĘCEJ</a>
                            <button class='like-btn' onclick='this.classList.toggle("active")'>❤</button>
                        </div>
                    </div>
                </div>"""
        except: continue

    szablon = f"""
    <html><head><meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body {{ background: #080808; color: #fff; font-family: 'Inter', sans-serif; margin: 0; scroll-behavior: smooth; }}
        
        /* NAWIGACJA */
        nav {{ background: #121212; border-bottom: 2px solid #f58426; position: sticky; top: 0; z-index: 1000; padding: 15px 0; }}
        .nav-wrap {{ max-width: 1200px; margin: auto; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; }}
        .nav-logo {{ font-weight: 900; font-size: 1.5rem; color: #f58426; }}
        .nav-links a {{ color: #888; text-decoration: none; margin-left: 20px; font-weight: bold; font-size: 0.8rem; }}
        .nav-links a:hover {{ color: #fff; }}

        /* LAYOUT */
        .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; max-width: 1200px; margin: 40px auto; padding: 0 20px; }}
        
        /* NEWSY */
        .section-title {{ font-size: 1.5rem; font-weight: 900; margin-bottom: 30px; border-left: 5px solid #1d428a; padding-left: 15px; text-transform: uppercase; color: #f58426; }}
        .card {{ background: #151515; border-radius: 12px; overflow: hidden; margin-bottom: 40px; border: 1px solid #222; position: relative; transition: 0.3s; }}
        .card:hover {{ transform: translateY(-5px); border-color: #f58426; }}
        .card img {{ width: 100%; height: 350px; object-fit: cover; }}
        .tag {{ position: absolute; top: 20px; left: 20px; background: #f58426; color: #000; padding: 4px 12px; border-radius: 4px; font-weight: 900; font-size: 0.7rem; }}
        .card-body {{ padding: 25px; }}
        h2 {{ margin: 0 0 15px 0; font-size: 1.8rem; line-height: 1.2; }}
        p {{ color: #bbb; line-height: 1.6; font-size: 1.1rem; }}
        
        /* SIDEBAR & LOGOWANIE */
        .login-box {{ background: #1a1a1a; padding: 20px; border-radius: 10px; margin-bottom: 30px; border: 1px dashed #333; }}
        .login-box h4 {{ margin: 0 0 10px 0; color: #f58426; }}
        input[type="text"] {{ width: 100%; padding: 10px; background: #222; border: 1px solid #333; color: #fff; border-radius: 5px; margin-bottom: 10px; box-sizing: border-box; }}
        
        /* WYNIKI */
        .sidebar-title {{ font-weight: 900; margin-bottom: 20px; color: #fff; text-transform: uppercase; }}
        .score-box {{ background: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #f58426; }}
        .score-teams {{ color: #777; font-size: 0.8rem; font-weight: bold; }}
        .score-value {{ font-size: 1.4rem; font-weight: 900; margin: 5px 0; color: #f58426; }}
        .score-status {{ font-size: 0.7rem; font-weight: bold; color: #1d428a; }}

        /* KOMENTARZE */
        .comment-section {{ background: #111; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .comment {{ font-size: 0.85rem; color: #999; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px solid #222; }}
        .comment b {{ color: #f58426; }}
        .comment-input-area {{ display: flex; gap: 8px; }}
        .comment-input-area button {{ background: #1d428a; color: #fff; border: none; padding: 0 15px; border-radius: 4px; cursor: pointer; font-weight: bold; }}

        .card-footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #222; padding-top: 20px; }}
        .btn {{ background: #f58426; color: #000; text-decoration: none; padding: 12px 25px; border-radius: 6px; font-weight: 900; }}
        .like-btn {{ background: none; border: none; color: #333; font-size: 1.5rem; cursor: pointer; transition: 0.3s; }}
        .like-btn.active {{ color: #e0245e; }}
    </style>
    <script>
        let currentUser = "Anonim";
        function login() {{
            const nick = document.getElementById('user-nick').value;
            if(nick.trim() !== "") {{
                currentUser = nick;
                document.getElementById('welcome-msg').innerHTML = "Witaj, <b>" + nick + "</b>!";
                document.getElementById('user-nick').style.display = 'none';
            }}
        }}
        function addComment(id) {{
            const input = document.getElementById('input-' + id);
            const list = document.getElementById('list-' + id);
            if(input.value.trim() !== "") {{
                const d = document.createElement('div');
                d.className = 'comment';
                d.innerHTML = '<b>' + currentUser + ':</b> ' + input.value;
                list.appendChild(d);
                input.value = "";
            }}
        }}
    </script>
    </head>
    <body>
        <nav><div class='nav-wrap'><div class='nav-logo'>NBA.PL</div><div class='nav-links'><a href='#wyroznione'>GŁÓWNA</a><a href='#analizy'>ANALIZY</a></div></div></nav>
        
        <div class='grid'>
            <div class='news-col'>
                <header style='margin-bottom:40px;'><h1>NBA<span>DAILY</span></h1><p>{teraz}</p></header>
                {news_html}
            </div>
            
            <div class='sidebar-col'>
                <div class='login-box'>
                    <h4 id='welcome-msg'>Zaloguj się, aby pisać</h4>
                    <input type='text' id='user-nick' placeholder='Twój Nick...' onchange='login()'>
                </div>
                
                <div class='sidebar-title'>Live Scores</div>
                {scores_html}
                
                <div class='score-box' style='background:#1d428a; border:none; color:white;'>
                    <p style='margin:0; font-size:0.8rem;'><b>LIVE TV:</b> Mecz gwiazd już w niedzielę!</p>
                </div>
            </div>
        </div>
    </body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(szablon)

if __name__ == "__main__": stworz_gazete()
