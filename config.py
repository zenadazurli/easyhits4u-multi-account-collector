# config.py - Configurazione per il multi-account collector

# LISTA DEGLI ACCOUNT DA UTILIZZARE
# Formato: email, password, nome_identificativo
ACCOUNTS = [
    {'email': 'dangiopiera+filippomesherda@gmail.com', 'password': 'BV36!dav$C', 'name': 'acc1'},
    {'email': 'piersilviogarrini+linadarini@gmail.com', 'password': 'GF45!!dave', 'name': 'acc2'},
    {'email': 'sandrominori50+ucecelu@gmail.com', 'password': 'DDnmVV45!!', 'name': 'acc3'},
    {'email': 'sandrominori50+ulonomizano@gmail.com', 'password': 'DDnmVV45!!', 'name': 'acc4'},
    {'email': 'sandrominori50+uzakabechi@gmail.com', 'password': 'DDnmVV45!!', 'name': 'acc5'},
]

# Numero massimo di account simultanei
MAX_CONCURRENT_ACCOUNTS = 5

# Ritardo tra l'avvio di un account e l'altro (secondi)
STAGGERED_START_DELAY = 3

# Tempo di attesa tra un tentativo e l'altro
REQUEST_TIMEOUT = 15

# URL di riferimento
REFERER_URL = "https://www.easyhits4u.com/?ref=nicolacaporale"
