#!/usr/bin/env python3
"""
API FastAPI pour BurkinaHeritage
=================================

Serveur backend RESTful 100% Open Source pour l'assistant culturel burkinabè.

Cette API expose le système RAG via des endpoints HTTP et permet au frontend
React de poser des questions et recevoir des réponses contextualisées.

Endpoints principaux:
    - POST /api/chat : Poser une question au système RAG
    - GET /api/health : Vérifier l'état de santé du serveur
    - GET /api/stats : Obtenir les statistiques du corpus
    - DELETE /api/clear : Effacer l'historique (compatibilité frontend)
    - GET /docs : Documentation interactive Swagger UI

Technologies:
    - FastAPI : Framework web moderne et rapide
    - Pydantic : Validation des données
    - CORS : Support cross-origin pour le frontend
    - Uvicorn : Serveur ASGI haute performance

Auteur : BurkinaHeritage Team
Date : Novembre 2025
Licence : Open Source
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime

# Import du système RAG
from rag_simple import BurkinaHeritageRAGSimple

# Créer l'application FastAPI avec métadonnées
app = FastAPI(
    title="BurkinaHeritage API",
    description="Assistant IA Culturel 100% Open Source sur le Burkina Faso - Hackathon 2025",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend (localhost:5173) d'accéder à l'API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier : ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser GET, POST, DELETE, etc.
    allow_headers=["*"],  # Autoriser tous les headers
)

# Initialiser le système RAG au démarrage
print("\n" + "=" * 70)
print("🚀 Démarrage du serveur BurkinaHeritage API")
print("=" * 70 + "\n")

rag_system = None

@app.on_event("startup")
async def startup_event():
    """
    Événement de démarrage du serveur.
    
    Initialise le système RAG au lancement de l'API pour :
    - Charger le corpus de documents
    - Initialiser ChromaDB
    - Préparer la collection vectorielle
    
    Raises:
        Exception: Si l'initialisation du RAG échoue
    """
    global rag_system
    try:
        rag_system = BurkinaHeritageRAGSimple()
        print("\n✅ API prête à recevoir des requêtes!\n")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation du RAG: {e}\n")
        raise


# Modèles Pydantic pour la validation des données

class ChatRequest(BaseModel):
    """
    Modèle de requête pour l'endpoint /api/chat.
    
    Attributes:
        question (str): Question posée par l'utilisateur (requis)
        use_llm (bool): Activer le LLM Hugging Face (défaut: False)
        n_results (int): Nombre de documents à rechercher (défaut: 5)
        conversation_history (List[Dict]): Historique de la conversation
    """
    question: str
    use_llm: Optional[bool] = False  # Par défaut, utiliser le fallback
    n_results: Optional[int] = 5
    conversation_history: Optional[List[Dict[str, str]]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Qu'est-ce que le balafon ?",
                "use_llm": False,
                "n_results": 5,
                "conversation_history": [
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"}
                ]
            }
        }


class Source(BaseModel):
    """Source d'un document"""
    title: str
    source: str
    category: str


class ChatResponse(BaseModel):
    """
    Modèle de réponse pour l'endpoint /api/chat.
    
    Attributes:
        question (str): Question qui a été posée
        answer (str): Réponse générée par le système RAG
        sources (List[Source]): Liste des sources utilisées
        timestamp (str): Horodatage ISO 8601
        processing_time_ms (int): Temps de traitement en millisecondes
    """
    question: str
    answer: str
    sources: List[Source]
    timestamp: str
    processing_time_ms: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Qu'est-ce que le balafon ?",
                "answer": "Le balafon est un instrument de percussion...",
                "sources": [
                    {
                        "title": "Les instruments traditionnels",
                        "source": "document.pdf - page 5",
                        "category": "culture"
                    }
                ],
                "timestamp": "2025-11-03T22:45:00",
                "processing_time_ms": 1250
            }
        }


class HealthResponse(BaseModel):
    """État de santé du serveur"""
    status: str
    message: str
    rag_initialized: bool
    total_documents: int
    timestamp: str


class StatsResponse(BaseModel):
    """Statistiques du système"""
    total_documents: int
    categories: Dict[str, int]
    sources: List[str]


# Routes de l'API

@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🇧🇫 BurkinaHeritage API",
        "description": "Assistant IA Culturel 100% Open Source",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "health": "GET /api/health",
            "stats": "GET /api/stats",
            "docs": "GET /docs"
        }
    }


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Vérifie l'état de santé du serveur"""
    return {
        "status": "healthy" if rag_system else "error",
        "message": "Système RAG opérationnel" if rag_system else "RAG non initialisé",
        "rag_initialized": rag_system is not None,
        "total_documents": len(rag_system.corpus) if rag_system else 0,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Retourne les statistiques du système"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé")
    
    # Compter les catégories
    categories = {}
    sources_set = set()
    
    for doc in rag_system.corpus:
        cat = doc.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        
        source = doc.get("source", "").split(" - ")[0]
        if source:
            sources_set.add(source)
    
    return {
        "total_documents": len(rag_system.corpus),
        "categories": categories,
        "sources": sorted(list(sources_set))
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Répond à une question sur la culture burkinabè
    
    - **question**: La question à poser
    - **use_llm**: Utiliser le LLM Hugging Face (nécessite token)
    - **n_results**: Nombre de documents à rechercher
    - **conversation_history**: Historique de la conversation
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé")
    
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question trop courte")
    
    try:
        # Mesurer le temps de traitement
        start_time = datetime.now()
        
        # Obtenir la réponse du système RAG avec historique
        result = rag_system.ask(
            question=request.question,
            use_llm=request.use_llm,
            conversation_history=request.conversation_history
        )
        
        # Calculer le temps de traitement
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Formater la réponse
        return {
            "question": result["question"],
            "answer": result["answer"],
            "sources": result["sources"],
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.delete("/api/clear", tags=["System"])
async def clear_conversation():
    """Efface l'historique de conversation (pour compatibilité frontend)"""
    return {
        "status": "success",
        "message": "Historique effacé"
    }


# Point d'entrée pour lancer le serveur
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🌍 Lancement du serveur BurkinaHeritage")
    print("=" * 70)
    print("\n📡 API accessible sur: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
