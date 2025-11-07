# Usa l'immagine ufficiale del Rasa SDK
FROM rasa/rasa-sdk:3.12.0-latest

# Passiamo all’utente root per poter usare apt
USER root

# Installa curl (e pulisci la cache APT per tenere l’immagine leggera)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

 RUN pip install msal requests

# Torna all’utente non-privilegiato usato da Rasa SDK

USER 1001
# Crea la directory di lavoro
WORKDIR /app

# Copia la directory delle azioni
COPY . /app/actions


# Avvia il server delle custom actions
CMD ["start", "--actions", "actions"]