/**
 * Service API pour BurkinaHeritage
 * Gère toutes les communications avec le backend FastAPI
 */

// Configuration depuis les variables d'environnement
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  endpoints: {
    chat: '/api/chat',
    health: '/api/health',
    stats: '/api/stats',
    clear: '/api/clear'
  },
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000 // 30 secondes
};

/**
 * Envoie une question au système RAG backend
 * 
 * @param {string} question - Question de l'utilisateur
 * @param {boolean} useLLM - Utiliser le LLM Hugging Face (défaut: false)
 * @param {Array} conversationHistory - Historique de la conversation (tableau de {role, content})
 * @returns {Promise<Object>} Réponse avec answer et sources
 */
export async function sendMessage(question, useLLM = false, conversationHistory = []) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

    const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.chat}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        use_llm: useLLM,
        n_results: 5,
        conversation_history: conversationHistory
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    return {
      success: true,
      answer: data.answer,
      sources: data.sources || [],
      timestamp: data.timestamp,
      processing_time: data.processing_time_ms
    };

  } catch (error) {
    console.error('❌ Erreur API:', error);
    
    // Messages d'erreur intelligents selon le type d'erreur
    let errorMessage = "Une erreur s'est produite. Veuillez réessayer.";
    
    if (error.name === 'AbortError') {
      errorMessage = "⏱️ La requête a pris trop de temps. Le serveur est peut-être surchargé.";
    } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      errorMessage = "🔌 Impossible de contacter le serveur. Vérifiez qu'il est démarré (port 8000).";
    } else if (error.message.includes('HTTP 500')) {
      errorMessage = "⚠️ Erreur serveur. Consultez les logs du backend.";
    }
    
    return {
      success: false,
      error: error.message,
      answer: errorMessage,
      sources: []
    };
  }
}

/**
 * Vérifie l'état de santé du serveur backend
 * 
 * @returns {Promise<Object>} État du serveur
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.health}`);
    
    if (!response.ok) {
      throw new Error('Serveur non disponible');
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Backend non disponible:', error);
    return {
      status: 'offline',
      rag_initialized: false,
      message: error.message
    };
  }
}

/**
 * Récupère les statistiques du corpus
 * 
 * @returns {Promise<Object>} Statistiques
 */
export async function getStats() {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.stats}`);
    
    if (!response.ok) {
      throw new Error('Impossible de récupérer les stats');
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Erreur stats:', error);
    return null;
  }
}

/**
 * Formate les sources pour l'affichage
 * 
 * @param {Array} sources - Tableau de sources
 * @returns {string} Sources formatées en texte
 */
export function formatSources(sources) {
  if (!sources || sources.length === 0) {
    return '';
  }

  let formatted = '\n\n📚 Sources :\n';
  sources.forEach((source, index) => {
    formatted += `${index + 1}. ${source.title}\n   📄 ${source.source}\n`;
  });

  return formatted;
}

export default {
  sendMessage,
  checkHealth,
  getStats,
  formatSources
};
