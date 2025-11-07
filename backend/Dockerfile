FROM rasa/rasa:3.6.21-full

USER root

# Manteniamo pip nella serie 23.x che accetta ancora "-any-"
RUN python -m pip install --no-cache-dir --upgrade "pip<25"  \
 && pip install --no-cache-dir \
      "numpy==1.24.4" \
      "h5py==3.9.0" \
      "spacy==3.6.1" --no-deps \
      "thinc==8.1.12"

# resto del Dockerfile...

# 2️⃣ Scarico il modello italiano
RUN python -m spacy download it_core_news_md

# 3️⃣ Resto invariato
WORKDIR /app
COPY . /app

RUN rasa train
ENV RASA_TELEMETRY_ENABLED=false
USER rasa
CMD ["run","-m","/app/models","--enable-api","--cors","*","--debug","--endpoints","/app/endpoints.yml"]




