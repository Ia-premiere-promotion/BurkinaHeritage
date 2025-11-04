#!/usr/bin/env python3
"""
Système RAG (Retrieval-Augmented Generation) pour BurkinaHeritage
==================================================================

Architecture 100% Open Source :
- Embeddings : ChromaDB DefaultEmbeddingFunction (all-MiniLM-L6-v2)
- Base vectorielle : ChromaDB (stockage local persistant)
- LLM : Hugging Face Inference API (Mistral-7B-Instruct) + Fallback local

Ce module implémente le pipeline RAG complet :
1. Indexation des documents culturels burkinabè
2. Recherche par similarité vectorielle
3. Génération de réponses contextualisées

Auteur : BurkinaHeritage Team
Date : Novembre 2025
Licence : Open Source
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions
import requests

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Importer Google Generative AI avec la nouvelle syntaxe
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-genai non installé. Installation: pip install google-genai")


class BurkinaHeritageRAGSimple:
    """
    Système RAG simplifié pour répondre aux questions sur la culture burkinabè.
    
    Ce système permet de :
    - Charger un corpus de documents culturels
    - Indexer les documents dans une base vectorielle
    - Rechercher les documents pertinents par similarité sémantique
    - Générer des réponses à partir du contexte récupéré
    
    Attributes:
        corpus (List[Dict]): Liste des documents chargés
        collection: Collection ChromaDB pour la recherche vectorielle
        hf_token (str): Token Hugging Face (optionnel)
        hf_api_url (str): URL de l'API Hugging Face
    """
    
    def __init__(
        self,
        corpus_path: str = "data/corpus.json",
        chroma_dir: str = "data/chroma_db"
    ):
        """
        Initialise le système RAG.
        
        Args:
            corpus_path (str): Chemin vers le fichier JSON contenant le corpus
            chroma_dir (str): Répertoire de stockage de ChromaDB
            
        Raises:
            FileNotFoundError: Si le fichier corpus n'existe pas
            json.JSONDecodeError: Si le corpus n'est pas un JSON valide
        """
        self.corpus_path = Path(corpus_path)
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Initialisation du système RAG BurkinaHeritage...")
        
        # Charger le corpus avec limite pour économiser la mémoire
        print(f"📚 Chargement du corpus: {self.corpus_path}")
        with open(self.corpus_path, 'r', encoding='utf-8') as f:
            full_corpus = json.load(f)
        
        # OPTIMISATION ULTRA pour Render Free (512MB RAM): Limiter à 100 documents
        max_docs = 100
        if len(full_corpus) > max_docs:
            print(f"⚠️  Limitation à {max_docs} documents (au lieu de {len(full_corpus)}) pour optimisation mémoire Render Free")
            self.corpus = full_corpus[:max_docs]
        else:
            self.corpus = full_corpus
        
        print(f"✅ {len(self.corpus)} documents chargés")
        
        # Initialiser ChromaDB avec embeddings RAPIDES
        # OPTIMISATION: Utiliser DefaultEmbeddingFunction (modèle pré-installé avec ChromaDB)
        print("🗄️  Initialisation de ChromaDB...")
        
        # Configuration allégée pour environnements à faible mémoire
        import chromadb.config
        settings = chromadb.config.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=settings
        )
        
        # OPTIMISATION: DefaultEmbeddingFunction = ONNX pré-installé (pas de téléchargement)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Configuration des LLMs (ordre de priorité)
        # 1. Gemini API (Google)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        if self.gemini_api_key and GEMINI_AVAILABLE:
            # Configurer avec la clé API
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
            print("✅ Gemini API configurée")
        else:
            self.gemini_client = None
            if not self.gemini_api_key:
                print("⚠️  GEMINI_API_KEY non définie (variable d'environnement)")
        
        # 2. Hugging Face (fallback)
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
        self.hf_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # Setup collection
        self._setup_collection()
        
        print("✅ Système RAG initialisé!\n")
    
    def _setup_collection(self):
        """
        Configure la collection ChromaDB pour stocker les embeddings.
        
        Tente de charger une collection existante, sinon en crée une nouvelle
        et indexe tous les documents du corpus.
        
        Note:
            La collection est nommée "burkina_culture" et stockée de manière persistante
        """
        collection_name = "burkina_culture"
        
        try:
            # Essayer de charger la collection existante
            self.collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"📂 Collection chargée: {self.collection.count()} documents")
            
        except Exception:
            # Créer une nouvelle collection
            print(f"🆕 Création de la collection...")
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Culture du Burkina Faso"}
            )
            self._index_documents()
    
    def _index_documents(self):
        """
        Indexe tous les documents du corpus dans ChromaDB.
        
        ULTRA-OPTIMISÉ pour environnements à très faible mémoire (512 MB).
        Les documents sont traités par micro-batches de 20 au lieu de 50.
        
        Process:
            1. Diviser le corpus en micro-batches de 20
            2. Pour chaque batch : extraire texte, métadonnées et IDs
            3. Ajouter à la collection ChromaDB
            4. Libérer agressivement la mémoire entre chaque batch
            5. Afficher la progression
        """
        print("🔄 Indexation des documents...")
        
        # OPTIMISATION ULTRA pour Render Free: Réduire la taille des batches à 10
        batch_size = 10  # Réduit de 20 à 10 pour Render Free (512MB RAM)
        
        for i in range(0, len(self.corpus), batch_size):
            batch = self.corpus[i:i + batch_size]
            
            # Préparer les données
            documents = [doc["content"] for doc in batch]
            metadatas = [
                {
                    "title": doc["title"],
                    "source": doc["source"],
                    "category": doc["category"]
                }
                for doc in batch
            ]
            ids = [f"doc_{doc['id']}" for doc in batch]
            
            # Ajouter à ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # OPTIMISATION MAXIMALE: Libérer agressivement la mémoire
            del documents, metadatas, ids, batch
            import gc
            gc.collect()
            
            # Afficher progression réduite (tous les 100 docs)
            if (i + batch_size) % 100 == 0 or (i + batch_size) >= len(self.corpus):
                print(f"  ✓ {min(i + batch_size, len(self.corpus))}/{len(self.corpus)} indexés")
        
        print("✅ Indexation terminée!")
    
    def search_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Recherche les documents les plus pertinents par similarité vectorielle.
        
        OPTIMISÉ: n_results=3 au lieu de 5 par défaut pour réduire la charge mémoire
        
        Utilise ChromaDB pour trouver les documents dont le contenu est sémantiquement
        proche de la requête. Filtre intelligemment par catégorie selon les mots-clés.
        Tente une expansion d'acronymes si la recherche initiale échoue.
        
        Args:
            query (str): Question ou requête de l'utilisateur
            n_results (int): Nombre de documents à retourner (défaut: 3, réduit de 5)
            
        Returns:
            List[Dict]: Liste des documents pertinents avec leur contenu et métadonnées
            
        Example:
            >>> rag.search_documents("Qu'est-ce que le balafon ?", n_results=3)
            [{"content": "...", "metadata": {"title": "...", "source": "..."}}]
        """
        # Détection intelligente de catégorie
        query_lower = query.lower()
        
        # Mots-clés culturels (on privilégie la catégorie culture)
        cultural_keywords = [
            "griot", "balafon", "djembé", "kora", "musique", "danse", "tradition",
            "masque", "fespaco", "siao", "artisan", "tissage", "poterie", "bronze",
            "cérémonie", "rite", "ancêtre", "chef", "roi", "royaume", "ethnie",
            "mossi", "peul", "bobo", "lobi", "gourounsi", "touareg"
        ]
        
        # Mots-clés architecturaux
        architectural_keywords = [
            "grenier", "case", "maison", "habitat", "construction", "architecture",
            "mosquée", "bâtiment", "édifice", "banco", "terre", "paille"
        ]
        
        # Déterminer les catégories à privilégier
        prefer_culture = any(kw in query_lower for kw in cultural_keywords)
        prefer_architecture = any(kw in query_lower for kw in architectural_keywords)
        
        # Récupérer plus de résultats pour filtrer ensuite
        n_fetch = n_results * 3 if (prefer_culture or prefer_architecture) else n_results
        
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_fetch, 15)  # Maximum 15 pour performance
        )
        
        documents = []
        for i in range(len(results['documents'][0])):
            doc = {
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i]
            }
            
            # Filtrage intelligent par catégorie
            category = doc['metadata'].get('category', '')
            
            # Si on cherche de la culture, on exclut l'architecture
            if prefer_culture and not prefer_architecture:
                if category == 'architecture':
                    continue
            
            documents.append(doc)
            
            # Arrêter quand on a assez de résultats
            if len(documents) >= n_results:
                break
        
        return documents[:n_results]
    
    def generate_answer_hf(self, question: str, context_docs: List[Dict], conversation_history: List[Dict] = None) -> str:
        """
        Génère une réponse intelligente avec Gemini.
        
        Stratégie hybride intelligente :
        - Si contexte trouvé : Gemini reformule + peut compléter/corriger
        - Si pas de contexte : Gemini répond avec ses propres connaissances
        
        Args:
            question (str): Question de l'utilisateur
            context_docs (List[Dict]): Documents de contexte (peut être vide)
            conversation_history (List[Dict]): Historique de la conversation
            
        Returns:
            str: Réponse générée par Gemini
        """
        if conversation_history is None:
            conversation_history = []
            
        # Vérifier si on a du contexte pertinent
        has_context = len(context_docs) > 0
        
        # Construire l'historique pour le prompt (derniers 6 messages max)
        history_text = ""
        if conversation_history and len(conversation_history) > 1:  # Au moins 2 messages (user + assistant)
            recent_history = conversation_history[-7:-1]  # Exclure le dernier (question actuelle)
            if recent_history:
                history_lines = []
                for msg in recent_history:
                    role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
                    content = msg.get("content", "")[:150]  # Limiter la longueur
                    history_lines.append(f"{role}: {content}")
                history_text = "\n".join(history_lines)
        
        if has_context:
            # Construire le contexte depuis la BD
            context = "\n\n".join([
                f"Document {i+1}:\n{doc['content'][:500]}"
                for i, doc in enumerate(context_docs[:3])
            ])
            
            # PROMPT HYBRIDE : Reformuler + Compléter/Corriger AVEC HISTORIQUE
            if history_text:
                prompt = f"""Tu es un assistant expert sur le Burkina Faso (culture, histoire, traditions).

HISTORIQUE DE LA CONVERSATION :
{history_text}

CONTEXTE TROUVÉ DANS MA BASE DE DONNÉES :
{context}

QUESTION DE L'UTILISATEUR : {question}

TA MISSION :
1. TIENS COMPTE de l'historique de conversation ci-dessus pour comprendre le contexte
2. Utilise les informations du contexte de ma base de données comme BASE
3. Reformule de manière claire et fluide (pas de copier-coller)
4. Tu peux COMPLÉTER avec tes propres connaissances si nécessaire
5. Si la question fait référence à quelque chose dans l'historique (comme "elle", "il", "le SIAO", etc.), utilise cet historique
6. Réponds de manière naturelle et informative (2-4 phrases)

IMPORTANT : Réponds de façon cohérente avec la conversation précédente.

RÉPONSE (en français, naturelle et complète) :"""
            else:
                prompt = f"""Tu es un assistant expert sur le Burkina Faso (culture, histoire, traditions).

CONTEXTE TROUVÉ DANS MA BASE DE DONNÉES :
{context}

QUESTION DE L'UTILISATEUR : {question}

TA MISSION :
1. Utilise les informations du contexte ci-dessus comme BASE
2. Reformule de manière claire et fluide (pas de copier-coller)
3. Tu peux COMPLÉTER avec tes propres connaissances si nécessaire
4. Tu peux CORRIGER si une information semble incorrecte
5. Réponds de manière naturelle et informative (2-4 phrases)

IMPORTANT : Même si le contexte ne répond pas parfaitement, utilise tes connaissances du Burkina Faso pour donner une réponse complète et utile.

RÉPONSE (en français, naturelle et complète) :"""
        else:
            # PAS DE CONTEXTE : Gemini répond en mode conversationnel AVEC HISTORIQUE
            if history_text:
                prompt = f"""Tu es BurkinaHeritage, un assistant sympathique et expert sur le Burkina Faso.

HISTORIQUE DE LA CONVERSATION :
{history_text}

QUESTION : {question}

TA MISSION :
- TIENS COMPTE de l'historique pour comprendre le contexte
- Si la question fait référence à la conversation précédente, utilise cet historique
- Si c'est une salutation → réponds chaleureusement
- Si c'est une question sur le Burkina Faso → réponds avec tes connaissances
- Reste naturel, sympathique et cohérent avec la conversation
- Réponds en français (1-3 phrases)

RÉPONSE (naturelle, sympathique et cohérente) :"""
            else:
                prompt = f"""Tu es BurkinaHeritage, un assistant sympathique et expert sur le Burkina Faso.

QUESTION : {question}

CONTEXTE : C'est une question conversationnelle ou aucune donnée spécifique n'est nécessaire.

TA MISSION :
- Si c'est une salutation (bonjour, salut, etc.) → réponds chaleureusement et brièvement
- Si c'est une question sur toi → explique que tu es un assistant sur le Burkina Faso
- Si c'est une question sur le Burkina Faso → réponds avec tes connaissances
- Reste naturel, sympathique et concis (1-3 phrases)
- Réponds en français

RÉPONSE (naturelle et sympathique) :"""
        
        # Méthode 1: GEMINI API (PRIORITÉ)
        gemini_error_message = None
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                answer = response.text.strip()
                if answer and len(answer) > 30:
                    context_status = "avec contexte BD" if has_context else "sans contexte (Gemini pur)"
                    print(f"✅ Réponse générée par Gemini ({context_status})")
                    return answer
            except Exception as e:
                error_str = str(e)
                print(f"⚠️  Erreur Gemini API: {e}")
                
                # Déterminer le type d'erreur et créer un message approprié
                if "503" in error_str or "overloaded" in error_str.lower():
                    gemini_error_message = "⚠️ Le service d'IA est temporairement surchargé. Veuillez réessayer dans quelques instants."
                elif "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    gemini_error_message = "⚠️ Limite d'utilisation atteinte. Veuillez réessayer dans quelques minutes."
                elif "401" in error_str or "unauthorized" in error_str.lower() or "api key" in error_str.lower():
                    gemini_error_message = "⚠️ Problème de configuration de l'API. Veuillez contacter l'administrateur."
                elif "network" in error_str.lower() or "connection" in error_str.lower():
                    gemini_error_message = "⚠️ Problème de connexion réseau. Veuillez vérifier votre connexion internet et réessayer."
                else:
                    gemini_error_message = "⚠️ Le service d'IA est temporairement indisponible. Veuillez réessayer ultérieurement."
        
        # Fallback si Gemini échoue
        if has_context:
            # Si on a du contexte mais Gemini a échoué, utiliser le fallback intelligent
            print("⚠️  Utilisation du fallback avec contexte")
            fallback_answer = self._fallback_answer(context_docs, question)
            # Ajouter le message d'erreur au début si Gemini a échoué
            if gemini_error_message:
                return f"{gemini_error_message}\n\nVoici les informations que j'ai trouvées dans ma base de données :\n\n{fallback_answer}"
            return fallback_answer
        else:
            # NOUVEAU : Essayer de chercher avec des termes plus généraux
            print("⚠️  Pas de contexte trouvé, recherche élargie...")
            
            # Termes généraux sur le Burkina Faso
            general_terms = [
                "Burkina Faso culture traditions",
                "histoire Burkina Faso",
                "patrimoine burkinabè"
            ]
            
            expanded_docs = []
            for term in general_terms:
                try:
                    results = self.collection.query(
                        query_texts=[term],
                        n_results=3
                    )
                    if results and results['documents'] and results['documents'][0]:
                        for i in range(len(results['documents'][0])):
                            expanded_docs.append({
                                "content": results['documents'][0][i],
                                "metadata": results['metadatas'][0][i]
                            })
                except Exception as e:
                    continue
            
            if expanded_docs:
                print(f"✅ Trouvé {len(expanded_docs)} documents généraux")
                fallback_answer = self._fallback_answer(expanded_docs[:5], question)
                # Ajouter le message d'erreur au début si Gemini a échoué
                if gemini_error_message:
                    return f"{gemini_error_message}\n\nVoici des informations générales sur le Burkina Faso :\n\n{fallback_answer}"
                return fallback_answer
            else:
                print("⚠️  Aucun document trouvé même avec recherche élargie")
                error_prefix = f"{gemini_error_message}\n\n" if gemini_error_message else ""
                return f"{error_prefix}Désolé, je n'ai pas d'information sur ce sujet dans ma base de données. Posez-moi des questions sur la culture, l'histoire, les traditions, l'artisanat ou l'architecture du Burkina Faso. Par exemple : 'Qu'est-ce que le SIAO ?', 'Parle-moi du FESPACO', 'Qui est Thomas Sankara ?'"
    
    def _fallback_answer(self, context_docs: List[Dict], question: str = "") -> str:
        """
        Génère une réponse reformulée basée sur le contexte (sans LLM externe).
        
        Cette fonction crée une synthèse intelligente en:
        1. Extrayant les passages les plus pertinents
        2. Les combinant de manière fluide
        3. Structurant la réponse de manière compréhensible
        
        Args:
            context_docs (List[Dict]): Documents de contexte
            question (str): Question posée par l'utilisateur
            
        Returns:
            str: Réponse reformulée et structurée
        """
        if not context_docs:
            return "Désolé, je n'ai pas trouvé d'information sur ce sujet dans ma base de données. Posez-moi des questions sur la culture, l'histoire, les traditions ou l'architecture du Burkina Faso."

        # Extraire les contenus des meilleurs documents
        best_docs = context_docs[:3]
        
        # Détecter le type de question
        question_lower = question.lower()
        is_what_question = any(word in question_lower for word in ["qu'est-ce", "c'est quoi", "what is", "définition"])
        is_general_culture = any(word in question_lower for word in ["culture", "traditions", "patrimoine", "burkinab"])
        
        # Construire une introduction contextuelle
        intro = ""
        if is_what_question:
            intro = "Voici ce que je peux vous dire : "
        elif is_general_culture:
            intro = "Concernant la culture burkinabè : "
        
        # Combiner les contenus de manière intelligente
        combined_content = []
        total_words = 0
        max_words = 250  # Limite pour éviter les réponses trop longues
        
        for doc in best_docs:
            content = doc.get('content', '').strip()
            if not content:
                continue
            
            # Diviser en phrases (gérer plusieurs délimiteurs)
            import re
            sentences = re.split(r'[.!?]\s+', content)
            
            # Ajouter les phrases les plus pertinentes
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 25:  # Ignorer les phrases trop courtes
                    continue
                
                # Éviter les répétitions
                if sentence in combined_content:
                    continue
                
                words = sentence.split()
                if total_words + len(words) > max_words:
                    break
                
                combined_content.append(sentence)
                total_words += len(words)
                
                if len(combined_content) >= 4:  # Maximum 4 phrases
                    break
            
            if total_words >= max_words or len(combined_content) >= 4:
                break
        
        if not combined_content:
            # Fallback ultime - prendre le premier document
            first_content = best_docs[0].get('content', '')
            if len(first_content) > 400:
                return intro + first_content[:400].strip() + "..."
            return intro + first_content
        
        # Assembler la réponse de manière fluide
        answer = intro + ' '.join(combined_content)
        
        # Nettoyer et formater
        answer = answer.strip()
        
        # S'assurer que la réponse se termine bien
        if not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        # Limiter la longueur totale
        if len(answer) > 600:
            answer = answer[:597] + "..."
        
        return answer
    
    def _needs_database_search(self, question: str) -> bool:
        """
        Détermine si la question nécessite une recherche dans la base de données.
        
        Args:
            question (str): Question de l'utilisateur
            
        Returns:
            bool: True si recherche BD nécessaire, False sinon
        """
        question_lower = question.lower().strip()
        
        # Mots-clés qui indiquent un besoin de recherche documentaire
        keywords_requiring_search = [
            # Culture
            "griot", "balafon", "djembé", "kora", "musique", "danse", "tradition",
            "masque", "fespaco", "siao", "artisan", "tissage", "poterie", "bronze",
            "cérémonie", "rite", "ancêtre", "chef", "roi", "royaume", "ethnie",
            "mossi", "peul", "bobo", "lobi", "gourounsi", "touareg",
            # Architecture
            "grenier", "case", "maison", "habitat", "construction", "architecture",
            "mosquée", "bâtiment", "édifice", "banco", "terre", "paille",
            # Histoire
            "histoire", "indépendance", "thomas sankara", "sankara", "mogho naba",
            "empire", "colonial", "français", "guerre",
            # Géographie/Lieux
            "ouagadougou", "bobo-dioulasso", "banfora", "ville", "région",
            # Questions explicites
            "qui est", "qu'est-ce que", "c'est quoi", "parle-moi de",
            "explique", "raconte", "définition", "signification"
        ]
        
        # Si un mot-clé est détecté → recherche BD
        return any(keyword in question_lower for keyword in keywords_requiring_search)
    
    def _simple_chat_response(self, question: str) -> str:
        """
        Réponse simple sans recherche BD pour conversation générale.
        
        Args:
            question (str): Question de l'utilisateur
            
        Returns:
            str: Réponse conversationnelle
        """
        question_lower = question.lower().strip()
        
        # Salutations
        greetings = ["bonjour", "bonsoir", "salut", "hello", "yo", "hey", "coucou"]
        if any(greeting in question_lower for greeting in greetings):
            return """Bonjour ! 👋

Je suis BurkinaHeritage, votre assistant culturel sur le Burkina Faso.

Posez-moi des questions sur la culture, l'histoire, les traditions, l'architecture... Je suis là pour vous aider ! 😊"""
        
        # Questions sur l'état
        if any(q in question_lower for q in ["comment tu vas", "ça va", "comment allez-vous"]):
            return "Je vais très bien, merci ! 😊 Prêt à répondre à vos questions sur le Burkina Faso !"
        
        # Questions sur l'identité
        if any(q in question_lower for q in ["qui es-tu", "qui êtes-vous", "ton nom", "tu es qui"]):
            return """Je suis **BurkinaHeritage**, un assistant culturel spécialisé dans le patrimoine du Burkina Faso. 🇧🇫

Je dispose de 370 documents sur la culture, l'architecture, l'histoire et bien plus encore.

Posez-moi des questions précises pour en savoir plus ! 📚"""
        
        # Questions sur les capacités
        if any(q in question_lower for q in ["que sais-tu", "que connais-tu", "que peux-tu", "tu connais quoi"]):
            return """Je connais beaucoup de choses sur le **Burkina Faso** ! 🇧🇫

Mes domaines d'expertise :
• 🎭 Culture (traditions, griots, musique, artisanat)
• 🏛️ Architecture traditionnelle
• 📚 Histoire et grands personnages
• 🎬 Événements culturels (FESPACO, SIAO...)
• 🌍 Patrimoine et société

Posez-moi une question spécifique ! 😊"""
        
        # Réponse par défaut pour conversation générale
        return """Je suis spécialisé dans le patrimoine du Burkina Faso. 

Pour que je puisse vous aider au mieux, posez-moi une question précise sur :
• La culture et les traditions
• L'histoire du pays
• L'architecture
• Les personnalités marquantes
• Les événements culturels

Que voulez-vous savoir ? 🤔"""
    
    def ask(self, question: str, use_llm: bool = True, conversation_history: List[Dict] = None) -> Dict:
        """
        Point d'entrée principal : TOUT passe par Gemini.
        
        Pipeline ultra-intelligent :
        1. Recherche dans la BD pour avoir du contexte
        2. Gemini répond TOUJOURS (conversation + reformulation + complétion)
        3. Sources affichées seulement si pertinentes
        
        Args:
            question (str): Question de l'utilisateur
            use_llm (bool): Toujours True (Gemini intelligent)
            conversation_history (List[Dict]): Historique de la conversation
            
        Returns:
            Dict: Dictionnaire contenant question, answer, sources
        """
        if conversation_history is None:
            conversation_history = []
            
        print(f"\n❓ Question: {question}")
        if conversation_history:
            print(f"📜 Historique: {len(conversation_history)} messages")
        
        # OPTIMISATION: Gérer les salutations et questions simples AVANT Gemini
        question_lower = question.lower().strip()
        simple_greetings = ["bonjour", "salut", "bonsoir", "coucou", "hey", "hello", "hi"]
        
        if question_lower in simple_greetings or any(g == question_lower for g in simple_greetings):
            print("👋 Salutation détectée - Réponse directe")
            return {
                "question": question,
                "answer": "Bonjour ! 👋 Je suis BurkinaHeritage, votre assistant culturel sur le Burkina Faso. Comment puis-je vous aider aujourd'hui ? 😊",
                "sources": []
            }
        
        # Déterminer si on recherche dans la BD
        needs_db = self._needs_database_search(question)
        
        if needs_db:
            # Question spécifique → rechercher dans la BD
            print("🔍 Recherche dans la base de données...")
            docs = self.search_documents(question, n_results=5)
            
            if docs:
                print(f"✅ {len(docs)} documents trouvés")
            else:
                print("⚠️  Aucun document trouvé")
        else:
            # Question conversationnelle → pas de recherche BD
            print("💬 Question conversationnelle")
            docs = []
        
        # GEMINI RÉPOND TOUJOURS (conversation + reformulation + complétion)
        print("🤖 Gemini génère la réponse...")
        answer = self.generate_answer_hf(question, docs, conversation_history)
        
        # Sources (seulement si on a cherché dans la BD ET trouvé des docs)
        sources = []
        if needs_db and docs:
            sources = [
                {
                    "title": doc['metadata']['title'],
                    "source": doc['metadata']['source'],
                    "category": doc['metadata']['category']
                }
                for doc in docs[:3]
            ]
        
        # Ajouter les sources APRÈS la réponse (seulement si pertinentes)
        answer_with_sources = answer.strip()
        if sources:
            source_lines = "\n".join([f"- {s['source']}" for s in sources])
            answer_with_sources = f"{answer_with_sources}\n\n\n📚 Sources :\n\n{source_lines}"

        return {
            "question": question,
            "answer": answer_with_sources,
            "sources": sources
        }


def main():
    """Test"""
    print("\n" + "=" * 70)
    print("🇧🇫 BurkinaHeritage RAG - Test")
    print("=" * 70 + "\n")
    
    rag = BurkinaHeritageRAGSimple()
    
    questions = [
        "Qu'est-ce que le balafon ?",
        "Parle-moi de l'architecture au Burkina Faso",
        "Qui sont les griots ?"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(questions)}")
        print("="*70)
        
        result = rag.ask(q, use_llm=False)  # Sans LLM pour le test
        
        print(f"\n📝 RÉPONSE:")
        print("-" * 70)
        print(result['answer'][:500])
        
        print(f"\n📚 SOURCES:")
        for j, s in enumerate(result['sources'], 1):
            print(f"  {j}. {s['source']}")
    
    print("\n✅ Tests terminés!\n")


if __name__ == "__main__":
    main()
