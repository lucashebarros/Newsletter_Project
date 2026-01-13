import feedparser
import google.generativeai as genai
import html2text
from datetime import datetime, timedelta
import os
import time
import requests # BIBLIOTECA PARA FALAR COM O BREVO
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from slugify import slugify

# Carrega a API Key do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO SUPABASE ---

SUPABASE_URL = "https://kwwipkcwxhlvrzlfkwyz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3d2lwa2N3eGhsdnJ6bGZrd3l6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODIzOTMyMCwiZXhwIjoyMDgzODE1MzIwfQ.PHYmOgrFhpmNDy-lXhmxKsX4fbJL270WHqegIm-8MHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO GEMINI ---
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- CONFIGURAÇÃO BREVO ---
BREVO_API_KEY = os.getenv("BREVO_API_KEY") # Vamos precisar adicionar isso no .env
# ID da lista de Cybersegurança (pegue no painel do Brevo)
BREVO_LIST_ID = 4 

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
    for tentativa in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            erro_str = str(e).lower()
            if "429" in erro_str or "quota" in erro_str or "resource" in erro_str:
                tempo = (tentativa + 1) * 60
                print(f"      ⚠️  Cota excedida. Esperando {tempo}s...")
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

# --- NOVA FUNÇÃO: ENVIAR EMAIL ---
def send_campaign(noticias):
    if not noticias:
        return

    print(f"\n📧 Preparando envio de e-mail com {len(noticias)} novidades...")

    # 1. Montar o HTML do E-mail
    hoje = datetime.now().strftime('%d/%m/%Y')
    html_content = f"<h1>🛡️ CyberDrop - Edição de {hoje}</h1><hr>"
    
    for news in noticias:
        # Converte markdown básico para HTML simples para o e-mail
        resumo_html = news['content'].replace('\n', '<br>').replace('**', '<b>')
        
        html_content += f"""
        <div style="margin-bottom: 30px; border-bottom: 1px solid #ccc; padding-bottom: 20px;">
            <h2 style="color: #2563eb;">{news['title']}</h2>
            <p>{resumo_html}</p>
            <a href="https://SEU-SITE-PAGES.dev/post/{news['slug']}" style="background: #000; color: #fff; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Ler no Site</a>
        </div>
        """
    
    html_content += "<br><p style='font-size: 12px; color: #666;'>Você recebeu isso porque se inscreveu no CyberDrop Hub.</p>"

    # 2. Criar a Campanha no Brevo via API
    url = "https://api.brevo.com/v3/emailCampaigns"
    
    payload = {
        "name": f"CyberDrop News - {hoje}",
        "subject": f"🔥 {len(noticias)} Alertas de Cybersegurança para hoje",
        "sender": {"name": "CyberDrop", "email": "SEU_EMAIL_CADASTRADO_NO_BREVO@GMAIL.COM"}, # <--- TROQUE AQUI
        "type": "classic",
        "htmlContent": html_content,
        "recipients": {"listIds": [BREVO_LIST_ID]}, # Manda para a lista Cyber
        "scheduledAt": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000+00:00') # Manda Agora (aproximado)
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }

    try:
        # Passo A: Criar Campanha
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            campaign_id = response.json().get('id')
            print(f"      ✅ Campanha criada! ID: {campaign_id}")
            
            # Passo B: Enviar Campanha Imediatamente
            send_url = f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow"
            requests.post(send_url, headers=headers)
            print("      🚀 E-mail enviado para a lista!")
        else:
            print(f"      ❌ Erro ao criar campanha: {response.text}")

    except Exception as e:
        print(f"      ❌ Erro na conexão com Brevo: {e}")

# --- MAIN ---

def main():
    print(f"🕵️  Iniciando varredura e disparo...\n")
    
    noticias_para_email = [] # Lista para juntar as novidades

    for url in FEEDS:
        print(f"📡 Lendo feed: {url}...")
        try:
            feed = feedparser.parse(url)
        except:
            continue
        
        for entry in feed.entries:
            if not is_recent(entry.get('published_parsed') or entry.get('updated_parsed')):
                continue

            text_content = entry.title + " " + entry.get('description', '')
            if not any(k.lower() in text_content.lower() for k in KEYWORDS):
                continue

            slug_base = slugify(entry.title)
            slug_final = f"{slug_base}-{datetime.now().strftime('%Y-%m-%d')}"

            if post_exists(slug_final):
                print(f"   ↪️  Pulando (Já existe): {entry.title[:30]}...")
                continue

            print(f"   🔥 [NOVA] Processando: {entry.title[:40]}...")
            clean_text = clean_html(entry.get('description', ''))
            resumo_ia = ai_summarize(entry.title, clean_text)
            
            if not resumo_ia: 
                time.sleep(5)
                continue

            data_insert = {
                "title": entry.title,
                "slug": slug_final,
                "content": resumo_ia,
                "category": "CYBER",
                "image_url": None
            }
            
            # Salva no Banco
            try:
                supabase.table("posts").insert(data_insert).execute()
                print("      ✅ Salvo no Banco!")
                
                # ADICIONA NA LISTA DE EMAIL
                noticias_para_email.append(data_insert)
                
            except Exception as e:
                print(f"      ❌ Erro ao salvar: {e}")

            time.sleep(20)

    # NO FINAL DE TUDO: Se tiver notícias novas, manda o e-mail
    if len(noticias_para_email) > 0:
        send_campaign(noticias_para_email)
    else:
        print("\n💤 Nenhuma notícia nova para enviar por e-mail hoje.")

    print(f"\n🏁 Fim.")

if __name__ == "__main__":
    main()