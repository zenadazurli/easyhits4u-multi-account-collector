# browserless_pool.py - Gestione pool di chiavi Browserless

import os
import time
import requests
from supabase import create_client
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurazione (da variabili d'ambiente)
BROWSERLESS_SUPABASE_URL = os.environ.get("BROWSERLESS_SUPABASE_URL")
BROWSERLESS_SUPABASE_KEY = os.environ.get("BROWSERLESS_SUPABASE_KEY")
BROWSERLESS_URL = "https://production-sfo.browserless.io/chrome/bql"

class BrowserlessPool:
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.load_keys()
    
    def load_keys(self):
        """Carica le chiavi Browserless dal database"""
        try:
            supabase = create_client(BROWSERLESS_SUPABASE_URL, BROWSERLESS_SUPABASE_KEY)
            resp = supabase.table('browserless_keys')\
                .select('api_key')\
                .eq('status', 'working')\
                .execute()
            
            self.keys = [item['api_key'] for item in resp.data] if resp.data else []
            print(f"📋 Caricate {len(self.keys)} chiavi Browserless")
        except Exception as e:
            print(f"❌ Errore caricamento chiavi: {e}")
            self.keys = []
    
    def get_next_key(self):
        """Restituisce la prossima chiave disponibile (round robin)"""
        if not self.keys:
            return None
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key
    
    def get_cf_token(self, api_key):
        """Ottiene il token Cloudflare usando Browserless"""
        query = """
        mutation {
          goto(url: "https://www.easyhits4u.com/logon/", waitUntil: networkIdle, timeout: 60000) {
            status
          }
          solve(type: cloudflare, timeout: 60000) {
            solved
            token
            time
          }
        }
        """
        url = f"{BROWSERLESS_URL}?token={api_key}"
        try:
            start = time.time()
            response = requests.post(url, json={"query": query}, 
                                    headers={"Content-Type": "application/json"}, 
                                    timeout=120)
            if response.status_code != 200:
                return None
            data = response.json()
            if "errors" in data:
                return None
            solve_info = data.get("data", {}).get("solve", {})
            if solve_info.get("solved"):
                token = solve_info.get("token")
                print(f"   ✅ Token ({time.time()-start:.1f}s)")
                return token
            return None
        except Exception as e:
            print(f"   ❌ Errore token: {e}")
            return None