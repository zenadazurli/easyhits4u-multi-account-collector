#!/usr/bin/env python3
# multi_account_collector.py - Multi-account collector per captcha matematici

import os
import time
import threading
import signal
import sys
from datetime import datetime

from config import ACCOUNTS, MAX_CONCURRENT_ACCOUNTS, STAGGERED_START_DELAY
from browserless_pool import BrowserlessPool
from captcha_collector import CaptchaCollector

# Variabili globali
running = True
active_threads = []

def signal_handler(sig, frame):
    global running
    print("\n🛑 Ricevuto segnale di stop, arresto in corso...")
    running = False

def run_collector(account):
    """Esegue il collector per un singolo account"""
    collector = CaptchaCollector(
        email=account['email'],
        password=account['password'],
        account_name=account['name'],
        browserless_pool=browserless_pool
    )
    collector.run()

def main():
    global running
    
    print("=" * 60)
    print("🚀 MULTI-ACCOUNT CAPTCHA COLLECTOR")
    print("=" * 60)
    print(f"📋 Account configurati: {len(ACCOUNTS)}")
    print(f"🔢 Massimo simultanei: {MAX_CONCURRENT_ACCOUNTS}")
    print("=" * 60)
    
    if not ACCOUNTS:
        print("❌ Nessun account configurato!")
        print("   Modifica il file config.py con i tuoi account")
        return
    
    # Inizializza pool Browserless
    global browserless_pool
    browserless_pool = BrowserlessPool()
    
    if not browserless_pool.keys:
        print("❌ Nessuna chiave Browserless disponibile!")
        return
    
    # Avvia collector per ogni account (con limitazione simultaneità)
    threads = []
    for i, account in enumerate(ACCOUNTS):
        if not running:
            break
        
        # Limita il numero di thread simultanei
        while len(threads) >= MAX_CONCURRENT_ACCOUNTS:
            # Rimuovi thread completati
            threads = [t for t in threads if t.is_alive()]
            time.sleep(1)
        
        print(f"\n📧 Avvio collector per account: {account['email']}")
        t = threading.Thread(target=run_collector, args=(account,))
        t.daemon = True
        t.start()
        threads.append(t)
        
        # Staggered start delay
        time.sleep(STAGGERED_START_DELAY)
    
    # Attendi il completamento di tutti i thread
    for t in threads:
        t.join(timeout=10)
    
    print("\n" + "=" * 60)
    print("✅ Raccolta completata!")
    print("=" * 60)
    print("📊 Statistiche finali:")
    print(f"   Account elaborati: {len(threads)}")
    print("   Controlla Supabase Storage per i captcha raccolti")
    print("=" * 60)

if __name__ == "__main__":
    # Gestisci segnale CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrotto dall'utente")
        sys.exit(0)