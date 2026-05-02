# captcha_collector.py - Modificato per usare SOLO cookie dal DB

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
    def __init__(self, email, account_name):  # RIMOSSO password e browserless_pool
        self.email = email
        self.account_name = account_name
        
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
        """Legge il cookie dal database per questa email"""
        try:
            supabase = create_client(self.supabase_url, self.supabase_key)
            resp = supabase.table('account_cookies')\
                .select('cookies_string')\
                .eq('email', self.email)\
                .eq('status', 'active')\
                .execute()
            
            if resp.data:
                self.log("✅ Cookie trovato su Supabase")
                return resp.data[0]['cookies_string']
            else:
                self.log("❌ Nessun cookie trovato per questa email")
                return None
        except Exception as e:
            self.log(f"❌ Errore lettura cookie: {e}")
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
        if image_path and os.path.exists(image_path):
            self.upload_captcha_to_supabase(image_path, surfses, urlid, qpic)
        self.log(f"📁 Captcha salvato")
        return True
    
    def run(self):
        """Esegue il collector per un account - usa SOLO cookie dal DB"""
        self.log(f"🚀 Avvio collector per account {self.email}")
        
        # Ottieni cookie dal database (SOLO QUESTO, NIENTE BROWSERLESS!)
        self.cookie_string = self.get_cookie_from_supabase()
        
        if not self.cookie_string:
            self.log("❌ Nessun cookie trovato nel database. Account saltato.")
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
                    self.log("⚠️ Cookie scaduto, passo al prossimo account")
                    break
                
                # Se è un captcha a figure, lo risolviamo
                if picmap is not None and len(picmap) > 0:
                    self.log("🎯 Captcha a figure - lo risolvo")
                    
                    # Cerca duplicati tra i valori di picmap
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
                
                # CAPTCHA MATEMATICO RILEVATO - SALVA E CONTINUA
                self.log("🧮 Captcha matematico rilevato - SALVO E CONTINUO")
                
                surfses = data.get("surfses", {})
                self.log(f"   Opzioni server: [{surfses.get('aword1_number')}, "
                        f"{surfses.get('aword2_number')}, {surfses.get('aword3_number')}]")
                
                # Scarica l'immagine
                img_data = self.session.get(f"https://www.easyhits4u.com/simg/{qpic}.jpg", 
                                            verify=False).content
                temp_path = f"temp_math_{self.account_name}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(img_data)
                
                # Salva
                self.save_captcha_error(surfses, urlid, qpic, temp_path)
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                self.log("🔄 Captcha salvato, continuo con il prossimo...")
                time.sleep(seconds)
                continue
                
            except Exception as e:
                self.log(f"❌ Errore: {e}")
                time.sleep(5)
                break
