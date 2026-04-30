# captcha_collector.py - Collettore di captcha matematici per singolo account

import os
import time
import requests
import cv2
import json
from datetime import datetime
from supabase import create_client
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CaptchaCollector:
    def __init__(self, email, password, account_name, browserless_pool):
        self.email = email
        self.password = password
        self.account_name = account_name
        self.browserless_pool = browserless_pool
        
        # Configurazione Supabase
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.math_supabase_url = os.environ.get("MATH_SUPABASE_URL")
        self.math_supabase_key = os.environ.get("MATH_SUPABASE_KEY")
        
        self.cookie_string = None
        self.session = None
    
    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}][{self.account_name}] {msg}")
    
    def get_cookie_from_supabase(self):
        """Legge il cookie dal database (se esiste per questa email)"""
        try:
            supabase = create_client(self.supabase_url, self.supabase_key)
            resp = supabase.table('account_cookies')\
                .select('cookies_string')\
                .eq('account_name', self.account_name)\
                .eq('email', self.email)\
                .eq('status', 'active')\
                .execute()
            
            if resp.data:
                self.log("✅ Cookie trovato su Supabase")
                return resp.data[0]['cookies_string']
            return None
        except Exception as e:
            self.log(f"❌ Errore lettura cookie: {e}")
            return None
    
    def save_cookie_to_supabase(self, cookie_string, user_id, sesids):
        """Salva il cookie nel database"""
        try:
            supabase = create_client(self.supabase_url, self.supabase_key)
            
            # Disattiva vecchi cookie per questo account/email
            supabase.table('account_cookies')\
                .update({'status': 'expired'})\
                .eq('account_name', self.account_name)\
                .eq('email', self.email)\
                .eq('status', 'active')\
                .execute()
            
            cookie_data = {
                'account_name': self.account_name,
                'email': self.email,
                'user_id': user_id,
                'cookies_string': cookie_string,
                'sesids': sesids,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('account_cookies').insert(cookie_data).execute()
            self.log("💾 Cookie salvato su Supabase")
            return True
        except Exception as e:
            self.log(f"⚠️ Errore salvataggio cookie: {e}")
            return False
    
    def generate_cookie(self):
        """Genera un nuovo cookie usando Browserless"""
        self.log("🔄 Generazione nuovo cookie...")
        
        api_key = self.browserless_pool.get_next_key()
        if not api_key:
            self.log("❌ Nessuna chiave Browserless disponibile")
            return None
        
        self.log(f"🔑 Usando chiave: {api_key[:15]}...")
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.easyhits4u.com/',
            'Origin': 'https://www.easyhits4u.com',
            'Connection': 'keep-alive',
        }
        
        try:
            # GET homepage
            session.get("https://www.easyhits4u.com/", headers=headers, verify=False, timeout=15)
            time.sleep(1)
            
            # Token Cloudflare
            token = self.browserless_pool.get_cf_token(api_key)
            if not token:
                return None
            
            # POST login
            login_headers = headers.copy()
            login_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            login_headers['Referer'] = "https://www.easyhits4u.com/?ref=nicolacaporale"
            data = {
                'manual': '1',
                'fb_id': '',
                'fb_token': '',
                'google_code': '',
                'username': self.email,
                'password': self.password,
                'cf-turnstile-response': token,
            }
            
            login_resp = session.post("https://www.easyhits4u.com/logon/", data=data, 
                                     headers=login_headers, allow_redirects=True, timeout=30)
            if login_resp.status_code != 200:
                return None
            
            time.sleep(2)
            session.get("https://www.easyhits4u.com/member/", headers=headers, verify=False, timeout=15)
            time.sleep(1)
            session.get("https://www.easyhits4u.com/surf/", headers=headers, verify=False, timeout=15)
            time.sleep(1)
            session.get("https://www.easyhits4u.com/?ref=nicolacaporale", headers=headers, verify=False, timeout=15)
            
            cookies = session.cookies.get_dict()
            
            if 'user_id' in cookies and 'sesids' in cookies:
                cookie_string = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                self.log(f"✅ Cookie generato! user_id={cookies['user_id']}")
                
                self.save_cookie_to_supabase(cookie_string, cookies['user_id'], cookies['sesids'])
                return cookie_string
            
            return None
            
        except Exception as e:
            self.log(f"   ❌ Errore: {e}")
            return None
    
    def upload_captcha_to_supabase(self, image_path, surfses, urlid, qpic):
        """Upload captcha su Supabase Storage"""
        try:
            if not self.math_supabase_url or not self.math_supabase_key:
                return False
            
            supabase_math = create_client(self.math_supabase_url, self.math_supabase_key)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
            
            with open(image_path, "rb") as f:
                file_data = f.read()
            
            file_path = f"{timestamp}/captcha.jpg"
            supabase_math.storage.from_("math-captchas").upload(file_path, file_data,
                                                               {"content-type": "image/jpeg"})
            
            self.log(f"📤 Captcha caricato su Supabase: {file_path}")
            return True
        except Exception as e:
            self.log(f"⚠️ Errore upload: {e}")
            return False
    
    def save_captcha_error(self, surfses, urlid, qpic, image_path):
        """Salva captcha matematico non riconosciuto"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        
        # Upload su Supabase
        if image_path and os.path.exists(image_path):
            self.upload_captcha_to_supabase(image_path, surfses, urlid, qpic)
        
        self.log(f"📁 Captcha salvato")
        return True
    
    def run(self):
        """Esegue il collector per un account - si ferma al primo captcha matematico"""
        self.log(f"🚀 Avvio collector per account {self.email}")
        
        # Ottieni cookie
        self.cookie_string = self.get_cookie_from_supabase()
        
        if not self.cookie_string:
            self.cookie_string = self.generate_cookie()
            if not self.cookie_string:
                self.log("❌ Impossibile ottenere cookie")
                return
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": self.cookie_string
        }
        self.session = requests.Session()
        self.session.headers.update(headers)
        
        while True:
            try:
                r = self.session.post("https://www.easyhits4u.com/surf/?ajax=1&try=1",
                                      verify=False, timeout=15)
                
                if r.status_code != 200:
                    time.sleep(5)
                    continue
                
                data = r.json()
                urlid = data.get("surfses", {}).get("urlid")
                qpic = data.get("surfses", {}).get("qpic")
                seconds = int(data.get("surfses", {}).get("seconds", 20))
                picmap = data.get("picmap")
                
                if not urlid or not qpic:
                    self.log("⚠️ Cookie scaduto")
                    break
                
                # Se è un captcha a figure, lo risolviamo
                if picmap is not None and len(picmap) > 0:
                    self.log("🎯 Captcha a figure - lo risolvo")
                    
                    # Scarica immagine e trova duplicato (logica semplificata)
                    img_data = self.session.get(f"https://www.easyhits4u.com/simg/{qpic}.jpg", 
                                                verify=False).content
                    
                    # Cerca duplicati tra i valori di picmap (simulazione)
                    values = [p.get("value") for p in picmap]
                    seen = {}
                    chosen_value = None
                    for i, val in enumerate(values):
                        if val in seen:
                            chosen_value = val
                            break
                        seen[val] = i
                    
                    if chosen_value:
                        time.sleep(seconds)
                        resp = self.session.get(
                            f"https://www.easyhits4u.com/surf/?f=surf&urlid={urlid}&surftype=2"
                            f"&ajax=1&word={chosen_value}&screen_width=1024&screen_height=768",
                            verify=False
                        )
                        if resp.json().get("warning") != "wrong_choice":
                            self.log("✅ Captcha figure risolto")
                        else:
                            self.log("❌ Errore su captcha figure")
                    else:
                        self.log("⚠️ Nessun duplicato trovato")
                    
                    time.sleep(2)
                    continue
                
                # CAPTCHA MATEMATICO RILEVATO - SALVA E FERMA
                self.log("🧮 Captcha matematico rilevato - SALVO E FERMO")
                
                surfses = data.get("surfses", {})
                self.log(f"   Opzioni server: [{surfses.get('aword1_number')}, "
                        f"{surfses.get('aword2_number')}, {surfses.get('aword3_number')}]")
                
                # Scarica l'immagine
                img_data = self.session.get(f"https://www.easyhits4u.com/simg/{qpic}.jpg", 
                                            verify=False).content
                temp_path = f"temp_math_{self.account_name}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(img_data)
                
                # Salva e ferma
                self.save_captcha_error(surfses, urlid, qpic, temp_path)
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                self.log("🛑 Collector fermato - captcha matematico raccolto")
                return
                
            except Exception as e:
                self.log(f"❌ Errore: {e}")
                time.sleep(5)
                break