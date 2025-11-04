import { useState, useEffect } from 'react';
import ChatMessage from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import { sendMessage, checkHealth } from './services/api';
import './App.css';

function App() {
  // État pour la sidebar
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth > 768);
  
  // État pour les conversations
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem('burkina_conversations');
    let initialConversations;
    
    if (saved) {
      try {
        initialConversations = JSON.parse(saved);
      } catch (e) {
        initialConversations = [{
          id: 1,
          title: 'Nouvelle conversation',
          date: new Date().toLocaleDateString('fr-FR'),
          messages: []
        }];
      }
    } else {
      initialConversations = [{
        id: 1,
        title: 'Nouvelle conversation',
        date: new Date().toLocaleDateString('fr-FR'),
        messages: []
      }];
    }
    
    return initialConversations;
  });
  
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    const saved = localStorage.getItem('burkina_conversations');
    if (saved) {
      try {
        const convs = JSON.parse(saved);
        const firstId = convs[0]?.id || 1;
        return firstId;
      } catch (e) {
        return 1;
      }
    }
    return 1;
  });
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online', 'offline', 'checking'

  // Vérifier l'état du backend au démarrage
  useEffect(() => {
    const checkBackend = async () => {
      const health = await checkHealth();
      setBackendStatus(health.status === 'healthy' ? 'online' : 'offline');
    };
    checkBackend();
  }, []);

  // Obtenir la conversation actuelle et ses messages
  const currentConversation = conversations.find(c => c.id === currentConversationId);
  const messages = currentConversation?.messages || [];


  // Sauvegarder les conversations dans localStorage
  useEffect(() => {
    localStorage.setItem('burkina_conversations', JSON.stringify(conversations));
  }, [conversations]);

  // Créer une nouvelle conversation
  const handleNewChat = () => {
    const newConv = {
      id: Date.now(),
      title: 'Nouvelle conversation',
      date: new Date().toLocaleDateString('fr-FR'),
      messages: [] // Pas de message initial
    };
    
    setConversations(prev => [newConv, ...prev]);
    setCurrentConversationId(newConv.id);
    
    // Fermer la sidebar sur mobile
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false);
    }
  };

  // Sélectionner une conversation
  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    
    // Fermer la sidebar sur mobile
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false);
    }
  };

  // Supprimer une conversation
  const handleDeleteConversation = (id) => {
    if (conversations.length === 1) {
      alert("Vous devez avoir au moins une conversation !");
      return;
    }
    
    const newConversations = conversations.filter(c => c.id !== id);
    setConversations(newConversations);
    
    // Si on supprime la conversation active, basculer vers la première
    if (id === currentConversationId) {
      setCurrentConversationId(newConversations[0].id);
    }
  };

  // Mettre à jour le titre de la conversation basé sur le premier message
  const updateConversationTitle = (conversationId, firstMessage) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId && conv.title === 'Nouvelle conversation') {
        return {
          ...conv,
          title: firstMessage.substring(0, 50) + (firstMessage.length > 50 ? '...' : '')
        };
      }
      return conv;
    }));
  };

  // Fonction pour envoyer un message
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

    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    // Récupérer les messages actuels avant la mise à jour
    const currentMessages = currentConversation?.messages || [];

    // Mettre à jour la conversation avec le nouveau message
    setConversations(prev => {
      const updated = prev.map(conv => {
        if (conv.id === currentConversationId) {
          const updatedMessages = [...conv.messages, userMessage];
          
          // Mettre à jour le titre si c'est le premier message utilisateur
          const updatedTitle = (conv.title === 'Nouvelle conversation' && conv.messages.length === 0)
            ? currentInput.substring(0, 50) + (currentInput.length > 50 ? '...' : '')
            : conv.title;
          
          return { ...conv, messages: updatedMessages, title: updatedTitle };
        }
        return conv;
      });
      return updated;
    });

    // Appeler l'API backend pour obtenir la réponse
    try {
      // Préparer l'historique de conversation pour l'API (derniers 10 messages)
      const conversationHistory = currentMessages.slice(-10).map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));
      
      // Ajouter le message actuel
      conversationHistory.push({
        role: 'user',
        content: currentInput
      });
      
      const response = await sendMessage(currentInput, true, conversationHistory); // use_llm = true pour Gemini
      
      // Créer un message AI vide pour l'animation
      const aiMessageId = Date.now() + 1;
      const aiMessage = {
        id: aiMessageId,
        text: '',
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources || [],
        isTyping: true
      };
      
      // Ajouter le message vide
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return { ...conv, messages: [...conv.messages, aiMessage] };
        }
        return conv;
      }));
      
      // Effet d'écriture lettre par lettre
      const fullText = response.answer;
      let currentText = '';
      let index = 0;
      
      const typingInterval = setInterval(() => {
        if (index < fullText.length) {
          currentText += fullText[index];
          index++;
          
          // Mettre à jour le message avec le texte progressif
          setConversations(prev => prev.map(conv => {
            if (conv.id === currentConversationId) {
              return {
                ...conv,
                messages: conv.messages.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, text: currentText }
                    : msg
                )
              };
            }
            return conv;
          }));
        } else {
          // Animation terminée
          clearInterval(typingInterval);
          
          // Marquer comme non en train de taper
          setConversations(prev => prev.map(conv => {
            if (conv.id === currentConversationId) {
              return {
                ...conv,
                messages: conv.messages.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, isTyping: false }
                    : msg
                )
              };
            }
            return conv;
          }));
        }
      }, 20); // 20ms par caractère pour un effet fluide
      
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      
      // Message d'erreur si l'API ne répond pas
      const errorMessage = {
        id: Date.now() + 1,
        text: "❌ Désolé, je ne peux pas répondre actuellement. Le serveur backend semble hors ligne. Assurez-vous qu'il est lancé avec 'python3 main.py' dans le dossier backend.",
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      };
      
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return { ...conv, messages: [...conv.messages, errorMessage] };
        }
        return conv;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  // Fonction pour effacer la conversation actuelle
  const handleClearChat = () => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === currentConversationId) {
        return {
          ...conv,
          title: 'Nouvelle conversation',
          messages: [] // Pas de message initial
        };
      }
      return conv;
    }));
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="app-wrapper">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
      />

      {/* Contenu principal */}
      <div className={`main-content ${isSidebarOpen ? 'with-sidebar' : ''}`}>
        {/* Header avec design culturel */}
        <header className="header">
          <button className="menu-toggle-btn" onClick={toggleSidebar} title="Menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18"/>
            </svg>
          </button>
          <div className="header-pattern"></div>
          <div className="header-content">
            <div className="logo">
              <div className="logo-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                  <polyline points="9 22 9 12 15 12 15 22"/>
                  <path d="M6 9h12"/>
                  <path d="M7 6h10"/>
                </svg>
              </div>
              <div className="logo-text">
                <h1>BurkinaHeritage</h1>
                <p className="subtitle">Assistant Culturel du Burkina Faso</p>
              </div>
            </div>
          </div>
        </header>

        {/* Zone principale de chat */}
        <main className="chat-container">
          <div className="chat-header">
            <button 
              className="clear-btn" 
              onClick={handleClearChat}
              title="Effacer la conversation"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              <span>Effacer</span>
            </button>
          </div>

          <div className="messages-container">
            {messages.length === 0 && !isLoading && (
              <div className="welcome-message">
                <div className="welcome-icon">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    <path d="M8 10h.01M12 10h.01M16 10h.01"/>
                  </svg>
                </div>
                <h2>Bienvenue sur BurkinaHeritage</h2>
                <p>Posez-moi des questions sur la culture, l'histoire, les traditions et le patrimoine du Burkina Faso.</p>
              </div>
            )}
            
            {messages.map((message) => (
              <ChatMessage 
                key={message.id} 
                message={message}
              />
            ))}
            
            {isLoading && (
              <div className="loading-message">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>L'IA réfléchit...</p>
              </div>
            )}
          </div>

          {/* Zone d'entrée utilisateur */}
          <form className="input-container" onSubmit={handleSendMessage}>
            <input
              type="text"
              className="chat-input"
              placeholder="Posez votre question sur la culture burkinabè..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="send-btn"
              disabled={isLoading || inputValue.trim() === ''}
            >
              <span>Envoyer</span>
              <span className="send-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2.5">
                  <path d="m22 2-7 20-4-9-9-4Z"/>
                  <path d="M22 2 11 13"/>
                </svg>
              </span>
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}

export default App;
