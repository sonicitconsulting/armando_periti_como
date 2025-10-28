# Configurazione per Instagram Prompt Generator
# Modifica questi parametri secondo le tue necessità

import os

class Config:
    """
    Configurazione centralizzata per il sistema RAG
    """

    # === CONFIGURAZIONE OLLAMA ===
    # Host del server Ollama (modifica se usi un server remoto)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://services.sonicitconsulting.it:10000")

    # Modello per l'embedding dei documenti
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "toshk0/nomic-embed-text-v2-moe:Q6_K")

    # Modello per l'analisi
    ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "llama3:instruct")

    # Modello per la generazione del post
    POST_MODEL = os.getenv("POST_MODEL", "llama3:latest")

    # === CONFIGURAZIONE CHROMADB ===
    # Path del database ChromaDB
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

    # Nome della collection
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "periti_como")

    # === CONFIGURAZIONE GRADIO ===
    # Porta per l'interfaccia web
    GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))

    # Condivisione pubblica (True per tunnel pubblico)
    GRADIO_SHARE = os.getenv("GRADIO_SHARE", "false").lower() == "true"

    # === CONFIGURAZIONE RAG ===
    # Numero di post simili da recuperare per l'analisi
    SIMILARITY_RESULTS = int(os.getenv("SIMILARITY_RESULTS", "3"))

    # Temperatura per la generazione (0.0 = deterministica, 1.0 = creativa)
    GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.4"))

    # === LIMITI E VALIDAZIONE ===
    # Lunghezza minima del contenuto del post (caratteri)
    MIN_POST_LENGTH = int(os.getenv("MIN_POST_LENGTH", "100"))

    # Lunghezza massima del prompt generato (caratteri)
    MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "8000"))

    ANALYSIS_PROMPT_FILE = os.getenv("ANALYSIS_PROMPT_FILE", "analysis_prompt.txt")
    GENERATION_PROMPT_FILE = os.getenv("GENERATION_PROMPT_FILE", "generation_prompt.txt")

    @classmethod
    def validate_config(cls):
        """
        Valida la configurazione e fornisce suggerimenti
        """
        issues = []

        # Verifica modelli Ollama
        required_models = [cls.EMBEDDING_MODEL, cls.ANALYSIS_MODEL]
        for model in required_models:
            if not model:
                issues.append(f"❌ Modello mancante: {model}")

        # Verifica path database
        if not cls.CHROMA_DB_PATH:
            issues.append("❌ Path database ChromaDB non specificato")

        # Verifica configurazione di rete
        if not cls.OLLAMA_HOST.startswith(('http://', 'https://')):
            issues.append(f"❌ Host Ollama non valido: {cls.OLLAMA_HOST}")

        if issues:
            print("🔧 Problemi di configurazione trovati:")
            for issue in issues:
                print(f"  {issue}")
            return False

        print("✅ Configurazione validata con successo")
        return True

    @classmethod  
    def print_config(cls):
        """
        Stampa la configurazione corrente
        """
        print("⚙️ CONFIGURAZIONE CORRENTE:")
        print(f"📡 Ollama Host: {cls.OLLAMA_HOST}")
        print(f"🧠 Modello Analisi: {cls.ANALYSIS_MODEL}")
        print(f"📊 Modello Embedding: {cls.EMBEDDING_MODEL}")
        print(f"💾 Database Path: {cls.CHROMA_DB_PATH}")
        print(f"🌐 Porta Gradio: {cls.GRADIO_PORT}")
        print(f"🔗 Condivisione: {'Abilitata' if cls.GRADIO_SHARE else 'Disabilitata'}")
