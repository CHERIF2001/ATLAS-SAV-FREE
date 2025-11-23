import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Mic, MicOff, Send, ArrowLeft, Loader2, X } from 'lucide-react';

interface ChatBotProps {
  onBack: () => void;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  isAnalyzing?: boolean;
}

const API_BASE_URL =
  ((import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_URL) ??
  'http://localhost:8000';

const quickButtons = [
  { id: 'network', label: 'Problème réseau', icon: '📶' },
  { id: 'billing', label: 'Facture', icon: '🧾' },
  { id: 'offer', label: 'Infos offre', icon: '📋' },
  { id: 'other', label: 'Autre demande', icon: '❓' }
];

export default function ChatBot({ onBack }: ChatBotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Bonjour ! Je suis l\'assistant virtuel de Free. Décrivez votre problème et je vous aiderai à le résoudre.',
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [ticketStatus, setTicketStatus] = useState<'en cours' | 'fermé'>('en cours');
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showQuickButtons, setShowQuickButtons] = useState(true);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return Date.now().toString();
  };

  const addMessage = (text: string, isUser: boolean, isAnalyzing = false) => {
    const newMessage: Message = {
      id: generateId(),
      text,
      isUser,
      timestamp: new Date(),
      isAnalyzing
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  };

  const updateMessage = (id: string, newText: string, isAnalyzing = false) => {
    setMessages(prev =>
      prev.map(message =>
        message.id === id ? { ...message, text: newText, isAnalyzing } : message
      )
    );
  };

  // Connexion WebSocket pour recevoir les mises à jour temps réel
  useEffect(() => {
    if (!ticketId) return;

    const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws/${ticketId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      // Log brut pour debug : montre exactement ce que le backend envoie
      console.debug('WS RAW:', event.data);
      const data = JSON.parse(event.data);

      if (data.type === 'new_message') {
        const msg = data.message;
        const newMsg: Message = {
          id: msg.id,
          text: msg.content,
          isUser: msg.role === 'user',
          timestamp: new Date(msg.timestamp),
          isAnalyzing: false
        };
        setMessages(prev => {
          // 1. Si le message existe déjà par ID (cas normal), on ne fait rien
          if (prev.some(m => m.id === msg.id)) return prev;

          // 2. Si c'est un message utilisateur, on cherche un doublon optimiste récent
          // pour remplacer le message temporaire par le message confirmé du serveur
          if (newMsg.isUser) {
            const now = new Date();
            // On cherche le dernier message utilisateur identique ajouté récemment (< 10s)
            // On parcourt en partant de la fin pour trouver le plus récent
            for (let i = prev.length - 1; i >= 0; i--) {
              const m = prev[i];
              if (m.isUser && m.text === newMsg.text && (now.getTime() - m.timestamp.getTime() < 10000)) {
                // On a trouvé le message optimiste correspondant
                const newMessages = [...prev];
                newMessages[i] = newMsg; // Remplacer par la version serveur (avec le bon ID)
                return newMessages;
              }
            }
          }

          return [...prev, newMsg];
        });
      } else if (data.type === 'ticket_snapshot') {
        // Charger l'historique complet du ticket
        const ticket = data.ticket;
        const loadedMessages: Message[] = ticket.messages.map((msg: any) => ({
          id: msg.id,
          text: msg.content,
          isUser: msg.role === 'user',
          timestamp: new Date(msg.timestamp),
          isAnalyzing: false
        }));
        // Remplacer les messages de bienvenue par l'historique réel
        if (loadedMessages.length > 0) {
          setMessages(loadedMessages);
        }
      } else if (data.type === 'status_updated') {
        // Gérer les mises à jour de statut
        console.log('Statut mis à jour:', data.status);
        setTicketStatus(data.status);
        if (data.status === 'fermé') {
          addMessage('Ce ticket a été fermé. Merci d\'avoir contacté le support Free.', false);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [ticketId]);

  const sendMessageToBackend = async (message: string) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) return;

    // Ajouter le message localement immédiatement (Optimistic UI)
    addMessage(trimmedMessage, true);
    setInputText('');
    setShowQuickButtons(false);

    const placeholderId = addMessage('Analyse en cours...', false, true);
    setIsAnalyzing(true);

    try {
      let response;

      if (!ticketId) {
        // Créer un nouveau ticket avec le premier message
        response = await fetch(`${API_BASE_URL}/public/tickets`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ initial_message: trimmedMessage })
        });

        if (!response.ok) {
          throw new Error('Erreur serveur');
        }

        const ticketData = await response.json();
        setTicketId(ticketData.ticket_id);

        // Ne pas mettre à jour manuellement, le WebSocket le fera
        // Supprimer le placeholder
        setMessages(prev => prev.filter(m => m.id !== placeholderId));
      } else {
        // Envoyer un message sur un ticket existant
        response = await fetch(`${API_BASE_URL}/public/tickets/${ticketId}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: trimmedMessage })
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Erreur serveur' }));
          throw new Error(errorData.detail || 'Erreur serveur');
        }

        // Ne pas mettre à jour manuellement, le WebSocket le fera
        // Supprimer le placeholder
        setMessages(prev => prev.filter(m => m.id !== placeholderId));
      }

      setIsAnalyzing(false);
    } catch (error) {
      console.error(error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur serveur';
      updateMessage(
        placeholderId,
        `Désolé, je ne parviens pas à contacter le serveur. ${errorMessage}`,
        false
      );
      setIsAnalyzing(false);
    }
  };

  const handleSendMessage = () => {
    sendMessageToBackend(inputText);
  };

  const handleQuickButton = (buttonId: string) => {
    const button = quickButtons.find(b => b.id === buttonId);
    if (!button) return;

    sendMessageToBackend(button.label);
  };

  const handleVoiceRecord = () => {
    if (isRecording) {
      // Arrêter l'enregistrement
      setIsRecording(false);
      sendMessageToBackend('Message vocal enregistré');
    } else {
      // Commencer l'enregistrement
      setIsRecording(true);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCloseTicket = async () => {
    if (!ticketId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/public/tickets/${ticketId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'fermé' })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la fermeture du ticket');
      }

      setTicketStatus('fermé');
      setShowCloseDialog(false);
      addMessage('Ce ticket a été fermé. Merci d\'avoir contacté le support Free.', false);
    } catch (error) {
      console.error('Erreur lors de la fermeture du ticket:', error);
      alert('Impossible de fermer le ticket. Veuillez réessayer.');
    }
  };

  // Fonction pour formater le texte avec support basique du markdown
  const formatMessage = (text: string): React.ReactElement => {
    // Séparer la signature "-- Agent Free" pour la styliser différemment
    // Utiliser [\s\S] pour capturer aussi les sauts de ligne (dotall)
    const signatureMatch = text.match(/([\s\S]*?)(\n*\s*--\s*Agent\s*Free\s*$)/i);
    const mainText = signatureMatch ? signatureMatch[1] : text;
    const signature = signatureMatch ? signatureMatch[2] : '';

    // Diviser en lignes et conserver les lignes vides (préservation du format)
    const lines = mainText.split('\n');

    return (
      <div className="space-y-2">
        {lines.map((line, index) => {
          const trimmedLine = line.trim();

          // Détecter les listes à puces (lignes commençant par - ou *)
          if (trimmedLine.match(/^[-*●]\s/)) {
            const content = trimmedLine.replace(/^[-*●]\s/, '');
            return (
              <div key={index} className="flex items-start gap-2 ml-1">
                <span className="mt-1 text-sm">•</span>
                <span className="flex-1">{formatInlineMarkdown(content)}</span>
              </div>
            );
          }

          // Détecter les numéros de liste (1. 2. etc.)
          const numberedMatch = trimmedLine.match(/^(\d+)\.\s(.+)/);
          if (numberedMatch) {
            return (
              <div key={index} className="flex items-start gap-2 ml-1">
                <span className="mt-0.5 font-medium text-sm min-w-[1.5rem]">{numberedMatch[1]}.</span>
                <span className="flex-1">{formatInlineMarkdown(numberedMatch[2])}</span>
              </div>
            );
          }

          // Ligne normale
          return (
            <div key={index} className={trimmedLine ? '' : 'h-2'}>
              {trimmedLine ? formatInlineMarkdown(trimmedLine) : null}
            </div>
          );
        })}
        {signature && (
          <div className="mt-3 pt-2 border-t border-gray-300/50">
            <p className="text-xs font-medium opacity-70 italic">{signature.trim()}</p>
          </div>
        )}
      </div>
    );
  };

  // Fonction pour formater le markdown inline (gras, italique)
  const formatInlineMarkdown = (text: string): (string | React.ReactElement)[] => {
    let keyIndex = 0;

    // D'abord traiter les gras **texte**
    const boldRegex = /\*\*(.+?)\*\*/g;
    let match;
    let lastIndex = 0;
    const boldParts: (string | React.ReactElement)[] = [];

    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        boldParts.push(text.substring(lastIndex, match.index));
      }
      boldParts.push(<strong key={`bold-${keyIndex++}`} className="font-semibold">{match[1]}</strong>);
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
      boldParts.push(text.substring(lastIndex));
    }

    // Ensuite traiter les italiques *texte* dans les parties texte restantes
    const finalParts: (string | React.ReactElement)[] = [];
    boldParts.forEach((part, partIndex) => {
      if (typeof part === 'string') {
        const italicRegex = /\*(.+?)\*/g;
        let italicLastIndex = 0;
        let italicMatch;
        let italicKeyIndex = 0;

        while ((italicMatch = italicRegex.exec(part)) !== null) {
          if (italicMatch.index > italicLastIndex) {
            finalParts.push(part.substring(italicLastIndex, italicMatch.index));
          }
          finalParts.push(<em key={`italic-${partIndex}-${italicKeyIndex++}`} className="italic">{italicMatch[1]}</em>);
          italicLastIndex = italicMatch.index + italicMatch[0].length;
        }
        if (italicLastIndex < part.length) {
          finalParts.push(part.substring(italicLastIndex));
        }
      } else {
        finalParts.push(part);
      }
    });

    return finalParts.length > 0 ? finalParts : [text];
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="bg-primary text-white p-4 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-white hover:bg-white/20"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold">F</span>
          </div>
          <div>
            <h1 className="font-semibold">Free</h1>
            <p className="text-xs text-white/80">
              Assistant virtuel
              {ticketStatus === 'fermé' && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded text-xs">Fermé</span>
              )}
            </p>
          </div>
        </div>
        {ticketId && ticketStatus === 'en cours' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCloseDialog(true)}
            className="text-white hover:bg-white/20"
            title="Fermer le ticket"
          >
            <X className="w-5 h-5" />
          </Button>
        )}
        {!ticketId || ticketStatus === 'fermé' ? <div className="w-10" /> : null}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.isUser
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-900'
                }`}
            >
              {message.isAnalyzing ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyse en cours...</span>
                </div>
              ) : (
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {formatMessage(message.text)}
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Boutons rapides */}
      {showQuickButtons && (
        <div className="p-4 border-t bg-gray-50">
          <p className="text-sm text-gray-600 mb-3">Ou choisissez rapidement :</p>
          <div className="grid grid-cols-2 gap-2">
            {quickButtons.map((button) => (
              <Button
                key={button.id}
                variant="outline"
                onClick={() => handleQuickButton(button.id)}
                className="h-12 text-xs border-primary/30 hover:bg-primary/10 hover:border-primary"
              >
                <span className="mr-2">{button.icon}</span>
                {button.label}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Zone de saisie */}
      <div className="p-4 border-t bg-white">
        {ticketStatus === 'fermé' && (
          <div className="mb-3 p-3 bg-gray-100 rounded-lg text-center text-sm text-gray-600">
            Ce ticket est fermé. Vous ne pouvez plus envoyer de messages.
          </div>
        )}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleVoiceRecord}
            disabled={ticketStatus === 'fermé'}
            className={`w-10 h-10 rounded-full ${isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
              } ${ticketStatus === 'fermé' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </Button>

          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={ticketStatus === 'fermé' ? "Ticket fermé" : "Écrire ici..."}
              disabled={ticketStatus === 'fermé'}
              className="pr-12"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isAnalyzing || ticketStatus === 'fermé'}
              className="absolute right-1 top-1/2 transform -translate-y-1/2 w-8 h-8 p-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Animation d'enregistrement vocal */}
        {isRecording && (
          <div className="mt-3 flex justify-center">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              <span className="ml-2 text-xs text-red-500">Enregistrement en cours...</span>
            </div>
          </div>
        )}
      </div>

      {/* Dialogue de confirmation de fermeture */}
      <Dialog open={showCloseDialog} onOpenChange={setShowCloseDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Fermer le ticket</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir fermer ce ticket ? Vous ne pourrez plus envoyer de messages après la fermeture.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-row gap-3 justify-end">
            <Button
              variant="outline"
              onClick={() => setShowCloseDialog(false)}
              className="flex-1 sm:flex-none"
            >
              Annuler
            </Button>
            <Button
              onClick={handleCloseTicket}
              className="flex-1 sm:flex-none bg-primary hover:bg-primary/90"
            >
              Fermer le ticket
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
