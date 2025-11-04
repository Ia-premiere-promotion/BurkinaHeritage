import './ChatMessage.css';

/**
 * Composant ChatMessage
 * Affiche un message dans la conversation (utilisateur ou IA)
 * 
 * Props:
 * - message: { id, text, sender, timestamp, sources }
 */
function ChatMessage({ message }) {
  const isAI = message.sender === 'ai';
  
  // Séparer le texte et les sources si présentes
  let mainText = message.text;
  let sources = [];
  let warningMessage = null;
  
  if (isAI && message.text) {
    // Détecter les messages d'avertissement (commence par ⚠️)
    const warningMatch = message.text.match(/^(⚠️[^\n]+)/);
    if (warningMatch) {
      warningMessage = warningMatch[1];
      // Retirer le warning du texte principal
      mainText = message.text.substring(warningMatch[0].length).trim();
    }
    
    // Chercher la section "Sources utilisées :" dans le texte
    const sourcesMatch = mainText.match(/Sources utilisées\s*:\s*([\s\S]*?)$/i);
    
    if (sourcesMatch) {
      // Extraire le texte avant les sources
      mainText = mainText.substring(0, sourcesMatch.index).trim();
      
      // Extraire les sources (lignes commençant par - ou •)
      const sourcesText = sourcesMatch[1];
      sources = sourcesText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('-') || line.startsWith('•'))
        .map(line => line.replace(/^[-•]\s*/, '').trim())
        .filter(line => line.length > 0);
    }
  }
  
  return (
    <div className={`message ${isAI ? 'message-ai' : 'message-user'}`}>
      <div className="message-avatar">
        {isAI ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="10" rx="2"/>
            <circle cx="12" cy="5" r="2"/>
            <path d="M12 7v4M8 16h.01M16 16h.01"/>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        )}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-sender">
            {isAI ? 'Assistant BurkinaHeritage' : 'Vous'}
          </span>
          <span className="message-time">{message.timestamp}</span>
        </div>
        {warningMessage && (
          <div className="message-warning">
            {warningMessage}
          </div>
        )}
        <div className="message-text">
          {mainText}
        </div>
        {sources.length > 0 && (
          <div className="message-sources">
            <div className="sources-title">Sources utilisées :</div>
            <ul className="sources-list">
              {sources.map((source, index) => (
                <li key={index}>{source}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
