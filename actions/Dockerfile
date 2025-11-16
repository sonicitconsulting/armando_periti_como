# Usa l'immagine ufficiale del Rasa SDK
FROM rasa/rasa-sdk:3.12.0-latest

# Passiamo all’utente root per poter usare apt
USER root

# Installa curl (e pulisci la cache APT per tenere l’immagine leggera)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

 RUN apt-get update \
    && apt-get install -y locales \
    && locale-gen it_IT.UTF-8 \
    && update-locale

RUN pip install requests google-api-python-client google-auth google-auth-oauthlib pytz

# Crea la directory di lavoro
WORKDIR /app

# Copia la directory delle azioni
COPY . /app/actions


# Avvia il server delle custom actions
CMD ["start", "--actions", "actions"]