import React, { useState, useRef, useEffect } from 'react';
import { EmailDocument } from './types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIChatPanelProps {
  emailDocument: EmailDocument;
  projectId: string;
  organizationId: string;
  emailId?: string;
  onApplyOperations: (operations: any[], explanation: string) => void;
}

const AIChatPanel: React.FC<AIChatPanelProps> = ({
  emailDocument,
  projectId,
  organizationId,
  emailId,
  onApplyOperations
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi! I\'m PewPew, your AI email design assistant. How can I help you create or improve this email?',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [proposedOperations, setProposedOperations] = useState<any[] | null>(null);
  const [proposalExplanation, setProposalExplanation] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Determine if we're modifying an existing email or creating a new one
      const isNewEmail = !emailId;
      
      // In a real implementation, this would call the backend API
      // For now, we'll simulate a response
      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: isNewEmail 
            ? "I'll create a professional email based on your request. Here's what I'm proposing:"
            : "I'll help modify your email based on your request. Here's what I'm suggesting:",
          timestamp: new Date()
        };

        // Simulate proposed operations
        const mockOperations = [
          {
            operation_type: "add_section",
            data: {
              type: "hero",
              props: {
                title: "Your Event Title",
                subtitle: "Join us for an amazing experience",
                alignment: "center"
              }
            },
            description: "Added a hero section with event title and subtitle"
          },
          {
            operation_type: "add_section",
            data: {
              type: "button",
              props: {
                label: "Register Now",
                url: "#",
                background_color: "#007bff",
                text_color: "#ffffff",
                alignment: "center"
              }
            },
            description: "Added a registration button"
          }
        ];

        setMessages(prev => [...prev, assistantMessage]);
        setProposedOperations(mockOperations);
        setProposalExplanation(isNewEmail 
          ? "I've created a compelling hero section to grab attention and added a clear call-to-action button for registration."
          : "I've enhanced the hero section to make it more engaging and added a prominent registration button."
        );
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const handleApplyChanges = () => {
    if (proposedOperations) {
      onApplyOperations(proposedOperations, proposalExplanation);
      setProposedOperations(null);
      setProposalExplanation('');
      
      const confirmationMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Changes applied successfully! Is there anything else you\'d like me to help with?',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, confirmationMessage]);
    }
  };

  const handleRejectChanges = () => {
    setProposedOperations(null);
    setProposalExplanation('');
    
    const rejectionMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: 'Changes discarded. Let me know if you\'d like me to suggest something else!',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, rejectionMessage]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="ai-chat-panel">
      <div className="chat-header">
        <h3>PewPew AI Assistant</h3>
        <p>Ask me to create or improve your email</p>
      </div>
      
      <div className="chat-messages">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`message ${message.role}`}
          >
            <div className="message-content">
              {message.content}
            </div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
        
        {proposedOperations && (
          <div className="proposal-card">
            <div className="proposal-header">
              <h4>Proposed Changes</h4>
              <p>{proposalExplanation}</p>
            </div>
            
            <div className="proposal-details">
              <ul>
                {proposedOperations.map((op, index) => (
                  <li key={index}>
                    <strong>{op.operation_type.replace('_', ' ')}</strong>: {op.description}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="proposal-actions">
              <button 
                className="apply-btn"
                onClick={handleApplyChanges}
              >
                Apply Changes
              </button>
              <button 
                className="reject-btn"
                onClick={handleRejectChanges}
              >
                Reject
              </button>
            </div>
          </div>
        )}
        
        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask PewPew to create or modify your email..."
          disabled={isLoading}
          rows={3}
        />
        <button 
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading}
          className="send-btn"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default AIChatPanel;