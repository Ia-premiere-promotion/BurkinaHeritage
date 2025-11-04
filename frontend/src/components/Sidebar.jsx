import { useState } from 'react';
import './Sidebar.css';

/**
 * Composant Sidebar - Navigation et historique des chats
 * Inspiré de l'interface ChatGPT
 */
function Sidebar({ 
  conversations, 
  currentConversationId, 
  onNewChat, 
  onSelectConversation,
  onDeleteConversation,
  isOpen,
  onToggle 
}) {
  const [searchQuery, setSearchQuery] = useState('');

  // Filtrer les conversations selon la recherche
  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Overlay pour mobile */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={onToggle}></div>
      )}

      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Header de la sidebar */}
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onNewChat}>
            <span className="icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
            </span>
            <span>Nouveau chat</span>
          </button>
          
          <button className="sidebar-close-btn" onClick={onToggle}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Barre de recherche */}
        <div className="sidebar-search">
          <input
            type="text"
            placeholder="Rechercher des chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <span className="search-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </span>
        </div>

        {/* Liste des conversations */}
        <div className="conversations-list">
          <div className="conversations-section">
            <h3 className="section-title">Conversations récentes</h3>
            {filteredConversations.length === 0 ? (
              <p className="no-conversations">Aucune conversation trouvée</p>
            ) : (
              filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`conversation-item ${
                    conv.id === currentConversationId ? 'active' : ''
                  }`}
                  onClick={() => onSelectConversation(conv.id)}
                >
                  <div className="conversation-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  </div>
                  <div className="conversation-info">
                    <div className="conversation-title">{conv.title}</div>
                    <div className="conversation-date">{conv.date}</div>
                  </div>
                  <button
                    className="delete-conversation-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    title="Supprimer"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer de la sidebar */}
        <div className="sidebar-footer">
          <div className="sidebar-menu">
            <a href="/about.html" className="menu-item" target="_blank">
              <span className="menu-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
              </span>
              <span>À propos</span>
            </a>
          </div>
          
          <div className="user-info">
            <div className="user-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div className="user-details">
              <div className="user-name">Utilisateur</div>
              <div className="user-status">En ligne</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
