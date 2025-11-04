// ====================================
// GUIDE D'INTÉGRATION API FASTAPI
// ====================================

/**
 * Ce fichier contient le code d'intégration avec le backend FastAPI
 * À utiliser dans App.jsx pour remplacer la simulation actuelle
 */

// ====================================
// 1. CONFIGURATION API
// ====================================

const API_CONFIG = {
  baseURL: 'http://localhost:8000',
  endpoints: {
    chat: '/api/chat',
    history: '/api/history',
    clear: '/api/clear'
  },
  timeout: 30000 // 30 secondes
};

// ====================================
// 2. SERVICE API
// ====================================

class BurkinaHeritageAPI {
  constructor(config) {
    this.config = config;
  }

  /**
   * Envoyer une question au système RAG
   * @param {string} question - Question de l'utilisateur
   * @returns {Promise<Object>} - Réponse de l'IA avec sources
   */
  async sendMessage(question) {
    try {
      const response = await fetch(`${this.config.baseURL}${this.config.endpoints.chat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: question,
          session_id: this.getSessionId() 
        }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        success: true,
        answer: data.answer,
        sources: data.sources || [],
        confidence: data.confidence || 0,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('API Error:', error);
      return {
        success: false,
        error: error.message,
        fallback: "Désolé, je ne peux pas répondre pour le moment. Veuillez réessayer."
      };
    }
  }

  /**
   * Récupérer l'historique de conversation
   * @returns {Promise<Array>} - Liste des messages
   */
  async getHistory() {
    try {
      const response = await fetch(
        `${this.config.baseURL}${this.config.endpoints.history}?session_id=${this.getSessionId()}`
      );
      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error('History Error:', error);
      return [];
    }
  }

  /**
   * Effacer l'historique
   */
  async clearHistory() {
    try {
      await fetch(`${this.config.baseURL}${this.config.endpoints.clear}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: this.getSessionId() })
      });
      return { success: true };
    } catch (error) {
      console.error('Clear Error:', error);
      return { success: false };
    }
  }

  /**
   * Obtenir ou créer un ID de session
   */
  getSessionId() {
    let sessionId = localStorage.getItem('burkina_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('burkina_session_id', sessionId);
    }
    return sessionId;
  }
}

// ====================================
// 3. INTÉGRATION DANS APP.JSX
// ====================================

/**
 * REMPLACER LA FONCTION handleSendMessage DANS App.jsx PAR:
 */

const api = new BurkinaHeritageAPI(API_CONFIG);

const handleSendMessage = async (e) => {
  e.preventDefault();
  
  if (inputValue.trim() === '') return;

  // Ajouter le message utilisateur
  const userMessage = {
    id: Date.now(),
    text: inputValue,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  };

  setMessages(prev => [...prev, userMessage]);
  const currentQuestion = inputValue;
  setInputValue('');
  setIsLoading(true);

  // Appel API réel
  const response = await api.sendMessage(currentQuestion);

  if (response.success) {
    // Formater la réponse avec les sources
    let answerText = response.answer;
    
    if (response.sources && response.sources.length > 0) {
      answerText += "\n\n📚 Sources:\n";
      response.sources.forEach((source, idx) => {
        answerText += `${idx + 1}. ${source.title} (${source.page || 'N/A'})\n`;
      });
    }

    const aiMessage = {
      id: Date.now() + 1,
      text: answerText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      sources: response.sources,
      confidence: response.confidence
    };
    
    setMessages(prev => [...prev, aiMessage]);
  } else {
    // Message d'erreur
    const errorMessage = {
      id: Date.now() + 1,
      text: response.fallback || "Une erreur est survenue. Veuillez réessayer.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      isError: true
    };
    
    setMessages(prev => [...prev, errorMessage]);
  }

  setIsLoading(false);
};

// ====================================
// 4. BACKEND FASTAPI (Python)
// ====================================

/**
 * Exemple de structure backend FastAPI
 * À créer dans: backend/main.py
 */

/*
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from langchain.llms import HuggingFaceHub
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma

app = FastAPI(title="BurkinaHeritage API")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class ChatRequest(BaseModel):
    question: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float

# Initialisation RAG
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 0.7})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = qa_chain({"query": request.question})
        
        sources = [
            {
                "title": doc.metadata.get("title", "Document sans titre"),
                "page": doc.metadata.get("page", "N/A"),
                "content": doc.page_content[:200]
            }
            for doc in result.get("source_documents", [])
        ]
        
        return ChatResponse(
            answer=result["result"],
            sources=sources,
            confidence=0.85  # À calculer selon votre logique
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history(session_id: str):
    # Implémenter la récupération de l'historique
    return {"messages": []}

@app.delete("/api/clear")
async def clear_history(request: dict):
    # Implémenter la suppression de l'historique
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
*/

// ====================================
// 5. INSTALLATION BACKEND
// ====================================

/*
# Créer l'environnement Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install fastapi uvicorn langchain chromadb sentence-transformers huggingface-hub

# Lancer le serveur
python backend/main.py

# Le backend sera disponible sur http://localhost:8000
# Documentation auto: http://localhost:8000/docs
*/

// ====================================
// 6. TEST DE L'API
// ====================================

/**
 * Test manuel de l'API avec curl
 */

/*
# Test de santé
curl http://localhost:8000/api/chat \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la capitale du Burkina Faso?", "session_id": "test123"}'

# Réponse attendue:
{
  "answer": "Ouagadougou est la capitale...",
  "sources": [...],
  "confidence": 0.95
}
*/

// ====================================
// 7. GESTION D'ERREURS
// ====================================

const handleAPIErrors = (error) => {
  const errorMessages = {
    'NetworkError': 'Problème de connexion. Vérifiez votre réseau.',
    'TimeoutError': 'Le serveur met trop de temps à répondre.',
    'HTTP 404': 'Point de terminaison API introuvable.',
    'HTTP 500': 'Erreur serveur. Contactez l\'administrateur.',
    'default': 'Une erreur inattendue est survenue.'
  };

  const errorType = error.name || error.message.split(':')[0];
  return errorMessages[errorType] || errorMessages.default;
};

// ====================================
// 8. EXPORT
// ====================================

export { BurkinaHeritageAPI, API_CONFIG, handleAPIErrors };
