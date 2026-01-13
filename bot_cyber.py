import feedparser
import google.generativeai as genai # Biblioteca Antiga
import html2text
from datetime import datetime, timedelta
import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from slugify import slugify

# Carrega a API Key do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO SUPABASE ---
# COLOQUE SUAS CHAVES AQUI
SUPABASE_URL = "https://kwwipkcwxhlvrzlfkwyz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3d2lwa2N3eGhsdnJ6bGZrd3l6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODIzOTMyMCwiZXhwIjoyMDgzODE1MzIwfQ.PHYmOgrFhpmNDy-lXhmxKsX4fbJL270WHqegIm-8MHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO GEMINI (BIBLIOTECA ANTIGA) ---
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# CORREÇÃO IMPORTANTE: Não existe gemini-2.5-flash. O correto é 1.5-flash.
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- FEEDS ---
FEEDS = [
    "https://www.gov.br/anpd/pt-br/assuntos/noticias/rss",
    "https://cisoadvisor.com.br/feed/",
    "https://www.conjur.com.br/secao/leis-e-negocios/protecao-de-dados/feed",
    "https://tecnoblog.net/assunto/seguranca/feed/",
]

KEYWORDS = [
    "vazamento", "leak", "ransomware", "lgpd", "anpd", 
    "multa", "password", "senha", "golpe", "phishing", 
    "ciso", "vulnerability", "cve", "zero-day"
]

DIAS_ATRAS = 1

# --- FUNÇÕES ---

def clean_html(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(html_content)

def is_recent(entry_date_struct):
    if not entry_date_struct: return True
    published = datetime(*entry_date_struct[:6])
    limit = datetime.now() - timedelta(days=DIAS_ATRAS)
    return published > limit

def ai_summarize(title, content):
    prompt = f"""
    Aja como o editor sênior de uma newsletter chamada 'CyberDrop'. 
    Analise esta notícia:
    Título: {title}
    Conteúdo: {content[:1500]}

    Gere um resumo em formato Markdown (sem repetir o título principal no topo).
    Estrutura:
    **O que rolou:** Resuma o fato em no máximo 2 frases diretas.
    **Por que importa:** Explique o impacto para um gestor de TI ou empresa.
    **O veredito:** Uma frase final com humor ácido e ironia.
    """
    # Tentativa com retry simples para a biblioteca antiga
    for tentativa in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            erro_str = str(e).lower()
            if "429" in erro_str or "quota" in erro_str or "resource" in erro_str:
                tempo = (tentativa + 1) * 60
                print(f"      ⚠️  Cota excedida (Erro 429). Esperando {tempo}s...")
                time.sleep(tempo)
                continue
            else:
                print(f"      ❌ Erro na IA: {e}")
                return None
    return None

def post_exists(slug):
    try:
        response = supabase.table("posts").select("id").eq("slug", slug).execute()
        return len(response.data) > 0
    except:
        return False

# --- MAIN ---

def main():
    print(f"🕵️  Iniciando varredura (Versão Legacy + Supabase)...\n")
    
    count_novos = 0

    for url in FEEDS:
        print(f"📡 Lendo feed: {url}...")
        try:
            feed = feedparser.parse(url)
        except:
            print(f"Erro ao ler {url}, pulando.")
            continue
        
        for entry in feed.entries:
            if not is_recent(entry.get('published_parsed') or entry.get('updated_parsed')):
                continue

            text_content = entry.title + " " + entry.get('description', '')
            if not any(k.lower() in text_content.lower() for k in KEYWORDS):
                continue

            # Gera Slug
            slug_base = slugify(entry.title)
            slug_final = f"{slug_base}-{datetime.now().strftime('%Y-%m-%d')}"

            if post_exists(slug_final):
                print(f"   ↪️  Pulando (Já existe): {entry.title[:30]}...")
                continue

            print(f"   🔥 [NOVA] Processando: {entry.title[:40]}...")
            
            clean_text = clean_html(entry.get('description', ''))
            
            # Gera resumo
            resumo_ia = ai_summarize(entry.title, clean_text)
            
            if not resumo_ia: 
                time.sleep(5)
                continue

            # Salva no Supabase
            try:
                data_insert = {
                    "title": entry.title,
                    "slug": slug_final,
                    "content": resumo_ia,
                    "category": "CYBER",
                    "image_url": None
                }
                
                supabase.table("posts").insert(data_insert).execute()
                print("      ✅ Salvo no Banco de Dados!")
                count_novos += 1
                
            except Exception as e:
                print(f"      ❌ Erro ao salvar no banco: {e}")

            # Pausa de segurança
            print("      ⏳ Pausa de 20s...")
            time.sleep(20)

    print(f"\n🏁 Fim. {count_novos} notícias enviadas para o site.")

if __name__ == "__main__":
    main()