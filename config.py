# config.py - Configurazione per il multi-account collector

# Lista degli account da utilizzare
# Formato: email, password, nome_identificativo
ACCOUNTS = [
    # Inserisci qui i tuoi account
    # {'email': 'dangiopiera+filippomesherda@gmail.com', 'password': 'BV36!dav$C', 'name': 'filippomesherda'},
    # {'email': 'piersilviogarrini+linadarini@gmail.com', 'password': 'BV36!dav$C', 'name': 'linadarini'},
    # {'email': 'sandrominori50+ucecelu@gmail.com', 'password': 'BV36!dav$C', 'name': 'uccelu'},
    # {'email': 'sandrominori50+uzakabechi@gmail.com', 'password': 'BV36!dav$C', 'name': 'uzakabechi'},
    # {'email': 'sandrominori50+ulonomizano@gmail.com', 'password': 'BV36!dav$C', 'name': 'unlomizano'},
]

# Numero massimo di account simultanei
MAX_CONCURRENT_ACCOUNTS = 5

# Ritardo tra l'avvio di un account e l'altro (secondi)
STAGGERED_START_DELAY = 3

# Tempo di attesa tra un tentativo e l'altro
REQUEST_TIMEOUT = 15

# URL di riferimento
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"