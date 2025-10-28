# Instagram Prompt Generator - Sistema RAG per Moellhausen
# Integra Ollama + ChromaDB + Gradio per generare prompt ottimali

import os
import gradio as gr
import chromadb
import ollama
import json
from typing import List, Dict, Optional
import re
from datetime import datetime
import pandas as pd

from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from gradio.themes.builder_app import variables

from  config import Config

class InstagramPromptGenerator:
    """
    Sistema RAG per generare prompt ottimali per post Instagram 
    mantenendo il tone of voice di Moellhausen
    """

    def __init__(
        self,
        chroma_path: str = Config.CHROMA_DB_PATH,
        collection_name: str = Config.COLLECTION_NAME,
        embedding_model: str = Config.EMBEDDING_MODEL,
        analysis_model: str = Config.ANALYSIS_MODEL,
        ollama_host: str = Config.OLLAMA_HOST,
        analysis_prompt: str = Config.ANALYSIS_PROMPT_FILE,
        generation_prompt: str = Config.GENERATION_PROMPT_FILE,
        post_generation_model: str = Config.POST_MODEL
    ):

        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.analysis_model = analysis_model
        self.ollama_host = ollama_host
        self.analysis_prompt = analysis_prompt
        self.generation_prompt = generation_prompt
        self.post_generation_model = post_generation_model

        # Configura client Ollama (per server remoto)
        if ollama_host != "http://localhost:11434":
            os.environ['OLLAMA_HOST'] = ollama_host

        embedding_func = OllamaEmbeddingFunction(
            model_name=Config.EMBEDDING_MODEL,
            url=Config.OLLAMA_HOST
        )

        # Inizializza ChromaDB
        os.makedirs(chroma_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Crea o ottieni la collection
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_func
            )
            print(f"Collection '{self.collection_name}' ready to be embedded via Ollama.\nModel: {Config.EMBEDDING_MODEL}")
        except Exception as e:
            print(f"Error during collection creation/retrieve: {e}")
            raise

    def extract_post_structure(self, post_text: str) -> Dict[str, str]:
        """
        Estrae la struttura del post Instagram utilizzando le sezioni markdown
        """
        sections = {
            'title': '',
            'brand_values': '',
            'introduction': '',
            'description': '',
            'closing': '',
            'olfactory_pyramid': '',
            'tags': ''
        }

        # Pattern per estrarre le sezioni
        current_section = None
        lines = post_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identifica le sezioni basandosi sui header
            if line.startswith('# '):
                sections['title'] = line[2:].strip()
                current_section = 'title'
            elif 'Brand Values' in line and line.startswith('##'):
                current_section = 'brand_values'
            elif 'Introduction' in line and line.startswith('##'):
                current_section = 'introduction'  
            elif 'Description' in line and line.startswith('##'):
                current_section = 'description'
            elif 'Closing' in line and line.startswith('##'):
                current_section = 'closing'
            elif 'OLFACTORY PYRAMID' in line and line.startswith('##'):
                current_section = 'olfactory_pyramid'
            elif 'TAGS' in line and line.startswith('##'):
                current_section = 'tags'
            elif current_section and not line.startswith('#'):
                # Aggiungi contenuto alla sezione corrente
                if sections[current_section]:
                    sections[current_section] += ' ' + line
                else:
                    sections[current_section] = line

        return sections

    def add_post_to_database(self, post_text: str, post_name: str = "") -> str:
        """
        Aggiunge un singolo post al database ChromaDB
        """
        try:
            # Crea un ID univoco
            post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if post_name:
                post_id = f"{post_name}_{post_id}"

            # Estrai la struttura del post
            structure = self.extract_post_structure(post_text)

            # Crea metadati con le informazioni estratte
            metadata = {
                'post_id': post_id,
                'title': structure['title'][:200] if structure['title'] else 'Untitled',
                'brand_values': structure['brand_values'][:300] if structure['brand_values'] else '',
                'date_added': datetime.now().isoformat(),
                'word_count': len(post_text.split()),
                'has_olfactory_pyramid': bool(structure['olfactory_pyramid']),
                'post_name': post_name or 'Unknown'
            }

            # Aggiungi alla collection ChromaDB
            self.collection.add(
                documents=[post_text],
                metadatas=[metadata],
                ids=[post_id]
            )

            return f"✅ Successfully added post '{structure['title'][:50]}...' (ID: {post_id})"

        except Exception as e:
            return f"❌ Error adding post: {str(e)}"

    def get_collection_stats(self) -> str:
        """
        Ottiene statistiche sulla collection
        """
        try:
            count = self.collection.count()
            if count == 0:
                return "📊 Empty database - No indexed post"

            # Prova a ottenere alcuni metadati per le statistiche
            sample = self.collection.get(limit=min(count, 5))
            titles = [meta.get('title', 'N/A')[:30] + '...' for meta in sample['metadatas']]

            stats = f"""📊 **Database statistics:**
                    - **Indexed posts:** {count}
                    - **Post examples:** {', '.join(titles)}
                    - **Database path:** {self.chroma_path}
                    """
            return stats

        except Exception as e:
            return f"❌ Error in calculating statistics: {str(e)}"

    def get_similar_posts(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Recupera i post più simili dalla database
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count())
            )

            similar_posts = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    similar_posts.append({
                        'document': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance  # Converti distanza in similarità
                    })

            return similar_posts

        except Exception as e:
            print(f"Error in retrieving similar posts: {str(e)}")
            return []

    def analyze_brand_voice(self, posts: List[Dict]) -> str:
        """
        Analizza il tone of voice e le caratteristiche dei post usando Ollama
        """
        if not posts:
            return "No post available for analysis"

        # Combina tutti i post per l'analisi
        combined_text = "\n\n---POST SEPARATOR---\n\n".join([post['document'] for post in posts])
        combined_text = combined_text[:3000]

        analysis_prompt_variables = {'combined_text': combined_text}

        analysis_prompt = self.load_prompt(self.analysis_prompt)

        try:
            analysis_prompt = analysis_prompt.format(**analysis_prompt_variables)
            client = ollama.Client(host=self.ollama_host)
            response = client.generate(
                model=self.analysis_model,
                prompt=analysis_prompt,
                options={'temperature': 0.3}
            )

            return response['response']

        except Exception as e:
            return f"❌ Error in brand voice analysis: {str(e)}"

    def generate_optimized_prompt(self, 
                                product_name: str,
                                perfumer_name: str, 
                                brand_values: str,
                                product_description: str,
                                olfactory_pyramid: str,
                                keywords: str) -> str:
        """
        Genera un prompt ottimizzato per LLM commerciale
        """
        try:
            # Verifica che ci siano dati nel database
            count = self.collection.count()
            if count == 0:
                return "❌ **Error:** No posts in the database. Please upload some sample posts first in the “Document Upload” section."

            # Recupera post simili basati su prodotto e valori
            query = f"{product_name} {brand_values} {product_description}"
            similar_posts = self.get_similar_posts(query, n_results=3)

            if not similar_posts:
                return "❌ **Error:** Unable to find similar posts in the database."

            post_examples = {chr(10).join(
                [f"ESEMPIO {i + 1}:{chr(10)}{post['document'][:1000]}..." for i, post in enumerate(similar_posts[:2])])}

            # Analizza il brand voice dei post simili
            brand_analysis = self.analyze_brand_voice(similar_posts)

            generation_prompt_variables = {"product_name": product_name,
                                "perfumer_name": perfumer_name,
                                "brand_values": brand_values,
                                "product_description": product_description,
                                "olfactory_pyramid": olfactory_pyramid,
                                "keywords": keywords,
                                "brand_analysis": brand_analysis,
                                "post_examples": post_examples}



            # Crea il prompt ottimizzato
            generation_prompt = self.load_prompt(self.generation_prompt)
            generation_prompt = generation_prompt.format(**generation_prompt_variables)

            client = ollama.Client(host=self.ollama_host, timeout=300)
            response = client.generate(
                model=self.analysis_model,
                prompt=generation_prompt,
                options={'temperature': 0.4, 'num_predict': 2000}
            )

            return response['response']

        except Exception as e:
            return f"❌ **Error generating prompt:** {str(e)}"

    def get_post_from_llm(self, prompt):

        try:
            client = ollama.Client(host=self.ollama_host)
            response = client.generate(
                model=self.post_generation_model,
                prompt=prompt,
                options={'temperature': 0.3}
            )

            return response['response']

        except Exception as e:
            return f"❌ Error in retrieving post: {str(e)}"


    def load_prompt(self, file_path: str) -> str:
        """Legge il prompt da file e sostituisce i placeholder."""
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        return prompt_template