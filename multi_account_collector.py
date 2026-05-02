#!/usr/bin/env python3
# multi_account_collector.py - Multi-account collector (SOLO COOKIE DB)

import os
import time
import threading
import signal
import sys

from config import ACCOUNTS, MAX_CONCURRENT_ACCOUNTS, STAGGERED_START_DELAY
from captcha_collector import CaptchaCollector

running = True

def signal_handler(sig, frame):
    global running
    print("\n🛑 Ricevuto segnale di stop, arresto in corso...")
    running = False

def run_collector(account):
    """Esegue il collector per un singolo account (senza Browserless)"""
    collector = CaptchaCollector(
        email=account['email'],
        account_name=account['name']
    )
    collector.run()

def main():
    global running
    
    print("=" * 60)
    print("🚀 MULTI-ACCOUNT CAPTCHA COLLECTOR (SOLO COOKIE DB)")
    print("=" * 60)
    print(f"📋 Account configurati: {len(ACCOUNTS)}")
    print(f"🔢 Massimo simultanei: {MAX_CONCURRENT_ACCOUNTS}")
    print("=" * 60)
    
    if not ACCOUNTS:
        print("❌ Nessun account configurato!")
        return
    
    threads = []
    for i, account in enumerate(ACCOUNTS):
        if not running:
            break
        
        while len(threads) >= MAX_CONCURRENT_ACCOUNTS:
            threads = [t for t in threads if t.is_alive()]
            time.sleep(1)
        
        print(f"\n📧 Avvio collector per account: {account['email']}")
        t = threading.Thread(target=run_collector, args=(account,))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(STAGGERED_START_DELAY)
    
    for t in threads:
        t.join(timeout=10)
    
    print("\n" + "=" * 60)
    print("✅ Raccolta completata!")
    print("=" * 60)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrotto dall'utente")
        sys.exit(0)
