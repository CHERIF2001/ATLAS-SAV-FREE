import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Mic, Phone, PhoneOff, ArrowLeft, MicOff, Pause, Volume2 } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';
// @ts-ignore - figma virtual asset handled by bundler
import freedaImage from 'figma:asset/452ef48d8f13b91872278532887faf790ae67cf3.png';

interface CallScreenProps {
  onBack: () => void;
}

export default function CallScreen({ onBack }: CallScreenProps) {
  const [callState, setCallState] = useState<'connecting' | 'calling' | 'ai-responding' | 'ended'>('connecting');
  const [timer, setTimer] = useState(0);
  const [connectingTimer, setConnectingTimer] = useState(10);
  const [isMuted, setIsMuted] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // Speech Recognition / Synthesis refs
  const recognitionRef = useRef<any>(null);
  const isSpeakingRef = useRef(false);

  // Phase 1: Connexion (10 secondes)
  useEffect(() => {
    if (callState === 'connecting') {
      const interval = setInterval(() => {
        setConnectingTimer((prev) => {
          if (prev <= 1) {
            setCallState('calling');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [callState]);

  // Phase 2: Appel en cours (timer qui monte)
  useEffect(() => {
    if (callState === 'calling') {
      const interval = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [callState]);

  // Simulation: après 30 secondes d'appel, l'IA répond
  useEffect(() => {
    if (callState === 'calling' && timer >= 30) {
      setCallState('ai-responding');
    }
  }, [callState, timer]);

  // Phase 3: IA répond (continue le timer)
  useEffect(() => {
    if (callState === 'ai-responding') {
      const interval = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [callState]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusText = () => {
    switch (callState) {
      case 'connecting':
        return 'Patientez, connexion à notre assistant vocal';
      case 'calling':
        return 'Voice Calling...';
      case 'ai-responding':
        return 'Connecté avec l\'assistant vocal de Free';
      case 'ended':
        return 'Appel terminé';
      default:
        return '';
    }
  };

  const getAIResponse = () => {
    if (callState === 'ai-responding') {
      return "Bonjour ! Je suis l'assistant virtuel de Free. Comment puis-je vous aider aujourd'hui ?";
    }
    if (callState === 'ended') {
      return "Merci d'avoir contacté Free. N'hésitez pas à nous recontacter si vous avez d'autres questions.";
    }
    return '';
  };

  // Détection simple de motif et génération de réponse
  const detectTopic = (message: string): string => {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes('réseau') || lowerMessage.includes('connexion') || lowerMessage.includes('wifi') || lowerMessage.includes('internet')) {
      return 'Problème réseau';
    }
    if (lowerMessage.includes('facture') || lowerMessage.includes('paiement') || lowerMessage.includes('prix') || lowerMessage.includes('coût')) {
      return 'Facture';
    }
    if (lowerMessage.includes('offre') || lowerMessage.includes('tarif') || lowerMessage.includes('forfait') || lowerMessage.includes('abonnement')) {
      return 'Infos offre';
    }
    return 'Autre demande';
  };

  const getResponseForTopic = (topic: string): string => {
    switch (topic) {
      case 'Problème réseau':
        return 'Je vois un souci de réseau. Souhaitez-vous diagnostiquer la box, le Wi‑Fi ou la ligne ?';
      case 'Facture':
        return 'Concernant votre facture, je peux vous aider à la consulter ou expliquer un montant. Que souhaitez‑vous faire ?';
      case 'Infos offre':
        return 'Pour nos offres, préférez‑vous des informations sur le mobile, l’internet ou la TV ?';
      default:
        return 'Bien noté. Pouvez‑vous préciser votre demande pour que je vous aide au mieux ?';
    }
  };

  // TTS helper
  const speak = (text: string) => {
    try {
      if (!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'fr-FR';
      utterance.rate = 1;
      utterance.pitch = 1;
      isSpeakingRef.current = true;
      utterance.onend = () => {
        isSpeakingRef.current = false;
      };
      window.speechSynthesis.speak(utterance);
    } catch {}
  };

  // ASR setup
  const startRecognition = () => {
    try {
      if (isMuted) return;
      const SpeechRecognitionImpl = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognitionImpl) return;
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }
      const recognition = new SpeechRecognitionImpl();
      recognition.lang = 'fr-FR';
      recognition.continuous = true;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const last = event.results[event.results.length - 1];
        if (!last || !last.isFinal) return;
        const transcript = last[0]?.transcript?.trim();
        if (!transcript) return;
        if (callState !== 'ai-responding') setCallState('ai-responding');
        const topic = detectTopic(transcript);
        const response = getResponseForTopic(topic);
        speak(response);
      };

      recognition.start();
      recognitionRef.current = recognition as any;
    } catch {}
  };

  const stopRecognition = () => {
    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }
      setIsListening(false);
    } catch {}
  };

  // Start/stop ASR with call state and mute
  useEffect(() => {
    if (callState === 'calling' || callState === 'ai-responding') {
      if (!isMuted) startRecognition();
      else stopRecognition();
    } else {
      stopRecognition();
    }
    return () => {
      stopRecognition();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callState, isMuted]);

  // Speak greeting when AI connects
  useEffect(() => {
    if (callState === 'ai-responding') {
      const greeting = getAIResponse();
      if (greeting) speak(greeting);
    }
    return () => {
      try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch {}
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callState]);

  // Pause/resume TTS
  useEffect(() => {
    try {
      if (!('speechSynthesis' in window)) return;
      if (isPaused) window.speechSynthesis.pause();
      else window.speechSynthesis.resume();
    } catch {}
  }, [isPaused]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecognition();
      try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch {}
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleBackAndCleanup = () => {
    stopRecognition();
    try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch {}
    onBack();
  };

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Image de fond avec overlay */}
      <div className="absolute inset-0">
        <ImageWithFallback
          src={freedaImage}
          alt="Freeda - Assistant virtuel"
          className="w-full h-full object-cover"
        />
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/40"></div>
      </div>

      {/* Contenu par-dessus */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <div className="flex items-center justify-between p-4 pt-8">
          <Button
            variant="ghost"
            onClick={handleBackAndCleanup}
            className="text-white hover:bg-white/20"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          
          {/* Indicateur audio en haut à droite */}
          {(callState === 'calling' || callState === 'ai-responding') && (
            <div className="bg-white/90 backdrop-blur-sm rounded-full px-3 py-2 flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-cyan-500" />
              <div className="flex items-end gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-cyan-500 rounded-full animate-pulse"
                    style={{
                      height: `${Math.random() * 12 + 4}px`,
                      animationDelay: `${i * 0.1}s`,
                    }}
                  />
                ))}
              </div>
              {isListening && (
                <span className="ml-2 text-xs text-cyan-700">Écoute...</span>
              )}
            </div>
          )}
        </div>

        {/* Informations du contact */}
        <div className="flex-1 flex flex-col justify-center items-center px-6">
          {callState === 'connecting' && (
            <div className="text-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-white/30 border-t-white mx-auto"></div>
              <h2 className="text-2xl">Free</h2>
              <p className="text-white/80">{getStatusText()}</p>
              <p className="text-lg font-mono text-white/60">{formatTime(connectingTimer)} secondes restantes</p>
            </div>
          )}

          {(callState === 'calling' || callState === 'ai-responding') && (
            <div className="text-center space-y-2">
              <div className="w-16 h-16 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center mb-4">
                <span className="text-2xl font-medium">F</span>
              </div>
              <h2 className="text-2xl">Free</h2>
              <p className="text-white/80">{getStatusText()}</p>
            </div>
          )}
        </div>

        {/* Timer d'appel */}
        {(callState === 'calling' || callState === 'ai-responding') && (
          <div className="text-center pb-8">
            <p className="text-3xl font-mono">{formatTime(timer)}</p>
          </div>
        )}

        {/* Ondes sonores animées */}
        {(callState === 'calling' || callState === 'ai-responding') && (
          <div className="flex justify-center items-end pb-8 space-x-1">
            {Array.from({ length: 20 }).map((_, i) => {
              const height = Math.random() * 30 + 10;
              const delay = i * 0.05;
              return (
                <div
                  key={i}
                  className="w-1 bg-white rounded-full animate-pulse"
                  style={{
                    height: `${height}px`,
                    animationDelay: `${delay}s`,
                    animationDuration: '1.5s',
                  }}
                />
              );
            })}
          </div>
        )}

        {/* Réponse IA */}
        {callState === 'ai-responding' && (
          <div className="mx-6 mb-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4">
              <p className="text-sm text-white/90">"{getAIResponse()}"</p>
            </div>
          </div>
        )}

        {/* Boutons de contrôle */}
        <div className="flex justify-center items-center gap-6 pb-12">
          {callState !== 'ended' && callState !== 'connecting' && (
            <>
              {/* Bouton Mute */}
              <Button
                variant="ghost"
                size="lg"
                onClick={() => setIsMuted(!isMuted)}
                className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white"
              >
                {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
              </Button>

              {/* Bouton Raccrocher */}
              <Button
                variant="destructive"
                size="lg"
                onClick={handleBackAndCleanup}
                className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600"
              >
                <PhoneOff className="w-7 h-7" />
              </Button>

              {/* Bouton Pause */}
              <Button
                variant="ghost"
                size="lg"
                onClick={() => setIsPaused(!isPaused)}
                className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white"
              >
                <Pause className="w-6 h-6" />
              </Button>
            </>
          )}

          {callState === 'ended' && (
            <Button
              onClick={onBack}
              className="flex items-center gap-2 px-8 py-3 rounded-full bg-green-600 hover:bg-green-700"
            >
              <Phone className="w-5 h-5" />
              Nouvel appel
            </Button>
          )}

          {callState === 'connecting' && (
            <Button
              variant="destructive"
              onClick={onBack}
              className="flex items-center gap-2 px-8 py-3 rounded-full"
            >
              <PhoneOff className="w-5 h-5" />
              Annuler
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}