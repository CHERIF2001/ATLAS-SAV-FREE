import React, { useState } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Checkbox } from './components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './components/ui/dialog';
import { Phone, MessageCircle, MessageSquare, Clock, Mail } from 'lucide-react';
import WhatsAppIcon from './components/WhatsAppIcon';
import CallScreen from './components/CallScreen';
import ChatBot from './components/ChatBot';
// @ts-ignore - figma virtual asset handled by bundler
import freeLogo from 'figma:asset/8a19c73fd0c06962d5eb8d13c5f61af1ebd6079d.png';

export default function App() {
  const [rgpdConsent, setRgpdConsent] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<'home' | 'call' | 'chat'>('home');
  const [showCallConfirmation, setShowCallConfirmation] = useState(false);
  const [showWhatsAppConfirmation, setShowWhatsAppConfirmation] = useState(false);
  const [showSMSConfirmation, setShowSMSConfirmation] = useState(false);
  const [showEmailConfirmation, setShowEmailConfirmation] = useState(false);

  // Détection mobile
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  const handleChannelSelect = (channel: string) => {
    if (!rgpdConsent) {
      alert('Veuillez accepter les conditions de traitement des données avant de continuer.');
      return;
    }
    
    if (channel === 'Téléphone') {
      setShowCallConfirmation(true);
    } else if (channel === 'WhatsApp') {
      setShowWhatsAppConfirmation(true);
    } else if (channel === 'SMS') {
      if (!isMobile) {
        alert('L\'option SMS n\'est disponible que sur mobile. Veuillez utiliser cette fonctionnalité depuis votre téléphone.');
        return;
      }
      setShowSMSConfirmation(true);
    } else if (channel === 'Email') {
      setShowEmailConfirmation(true);
    } else if (channel === 'Chat') {
      setCurrentScreen('chat');
    } else {
      // Pour les autres canaux, afficher un message temporaire
      console.log(`Canal sélectionné: ${channel}`);
      alert(`Vous avez choisi: ${channel} - Fonctionnalité à venir`);
    }
  };

  const handleConfirmCall = () => {
    setShowCallConfirmation(false);
    setCurrentScreen('call');
  };

  const handleCancelCall = () => {
    setShowCallConfirmation(false);
  };

  const handleConfirmWhatsApp = () => {
    setShowWhatsAppConfirmation(false);
    
    // Numéro WhatsApp du support Free (exemple)
    const phoneNumber = "+33634374398"; // Remplacez par le vrai numéro
    const message = "Bonjour, je souhaite contacter le support Free. Pouvez-vous m'aider ?";
    
    // Créer les liens WhatsApp
    const whatsappWebUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
    const whatsappAppUrl = `whatsapp://send?phone=${phoneNumber}&text=${encodeURIComponent(message)}`;
    
    // Détection mobile simple
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
      // Sur mobile, essayer d'ouvrir l'app WhatsApp d'abord
      const link = document.createElement('a');
      link.href = whatsappAppUrl;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Fallback vers WhatsApp Web après 2 secondes si l'app ne s'ouvre pas
      setTimeout(() => {
        window.open(whatsappWebUrl, '_blank');
      }, 2000);
    } else {
      // Sur desktop, ouvrir WhatsApp Web directement
      window.open(whatsappWebUrl, '_blank');
    }
  };

  const handleCancelWhatsApp = () => {
    setShowWhatsAppConfirmation(false);
  };

  const handleConfirmSMS = () => {
    setShowSMSConfirmation(false);
    
    // Numéro SMS du support Free (même numéro que WhatsApp)
    const phoneNumber = "+33666078215";
    const message = "Bonjour, je souhaite contacter le support Free. Pouvez-vous m'aider ?";
    
    // Créer le lien SMS
    const smsUrl = `sms:${phoneNumber}?body=${encodeURIComponent(message)}`;
    
    // Ouvrir l'application de messagerie native
    window.location.href = smsUrl;
  };

  const handleCancelSMS = () => {
    setShowSMSConfirmation(false);
  };

  const handleConfirmEmail = () => {
    setShowEmailConfirmation(false);
    
    // Adresse email du support Free
    const emailAddress = "support@free.fr";
    const subject = "Demande de support - Contact SAV";
    const body = `Bonjour,

Je souhaite contacter le support Free pour une demande formelle.

Détails de ma demande :
- [Veuillez décrire votre problème ou votre question]

Informations de contact :
- Nom : [Votre nom]
- Numéro de client : [Votre numéro de client si disponible]
- Téléphone : [Votre numéro de téléphone]

Cordialement,
[Votre nom]`;
    
    // Créer le lien mailto
    const mailtoUrl = `mailto:${emailAddress}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    // Ouvrir le client email par défaut
    window.location.href = mailtoUrl;
  };

  const handleCancelEmail = () => {
    setShowEmailConfirmation(false);
  };

  const handleBackToHome = () => {
    setCurrentScreen('home');
  };

  // Affichage conditionnel des écrans
  if (currentScreen === 'call') {
    return <CallScreen onBack={handleBackToHome} />;
  }
  
  if (currentScreen === 'chat') {
    return <ChatBot onBack={handleBackToHome} />;
  }

  return (
    <div className="min-h-screen bg-background p-4 flex items-center justify-center">
      <div className="w-full max-w-md mx-auto space-y-6">
        {/* En-tête avec logo Free */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center">
            <img 
              src={freeLogo} 
              alt="Free"
              className="h-16 w-auto"
            />
          </div>
          <h1 className="text-primary">Contactez le support Free</h1>
          <p className="text-muted-foreground">
            Choisissez votre méthode de contact préférée. Notre équipe est là pour vous aider.
          </p>
        </div>

        {/* Service 24/7 */}
        <Card className="border-2 border-primary/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-center gap-2 text-primary">
              <Clock className="w-5 h-5" />
              <span className="font-medium">Service disponible 24/7</span>
            </div>
          </CardContent>
        </Card>

        {/* Boutons de canal */}
        <Card>
          <CardHeader>
            <CardTitle>Choisissez votre canal de communication</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              variant="outline"
              className="w-full h-14 flex items-center justify-start gap-3 border-primary/30 hover:bg-accent hover:border-primary"
              onClick={() => handleChannelSelect('Téléphone')}
            >
              <Phone className="w-6 h-6 text-primary" />
              <span>Appeler</span>
            </Button>

            <Button
              variant="outline"
              className="w-full h-14 flex items-center justify-start gap-3 border-primary/30 hover:bg-accent hover:border-primary"
              onClick={() => handleChannelSelect('Chat')}
            >
              <MessageCircle className="w-6 h-6 text-primary" />
              <span>Écrire un message</span>
            </Button>

            <Button
              variant="outline"
              className={`w-full h-14 flex items-center justify-start gap-3 border-primary/30 hover:bg-accent hover:border-primary ${
                !isMobile ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              onClick={() => handleChannelSelect('SMS')}
              disabled={!isMobile}
            >
              <MessageSquare className="w-6 h-6 text-primary" />
              <span>SMS {!isMobile && '(Mobile uniquement)'}</span>
            </Button>

            <Button
              variant="outline"
              className="w-full h-14 flex items-center justify-start gap-3 border-primary/30 hover:bg-accent hover:border-primary"
              onClick={() => handleChannelSelect('WhatsApp')}
            >
              <WhatsAppIcon className="w-6 h-6 text-primary" />
              <span>WhatsApp</span>
            </Button>

            <Button
              variant="outline"
              className="w-full h-14 flex items-center justify-start gap-3 border-primary/30 hover:bg-accent hover:border-primary"
              onClick={() => handleChannelSelect('Email')}
            >
              <Mail className="w-6 h-6 text-primary" />
              <span>Email (Demande formelle)</span>
            </Button>
          </CardContent>
        </Card>

        {/* Politique de confidentialité*/}
        <Card className="border-primary/30 bg-accent/50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <Checkbox 
                id="rgpd-consent"
                checked={rgpdConsent}
                onCheckedChange={(checked) => setRgpdConsent(checked === true)}
                className="border-primary data-[state=checked]:bg-primary data-[state=checked]:border-primary"
              />
              <div className="grid gap-1.5 leading-none">
                <label 
                  htmlFor="rgpd-consent"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Politique de confidentialité
                </label>
                <p className="text-xs text-muted-foreground">
                  J'accepte que mes données personnelles soient traitées dans le cadre de ma demande de support, 
                  conformément à notre politique de confidentialité. Vous pouvez retirer votre consentement à tout moment. 
                  <a
                    href="https://free.fr/politique-confidentialite/conservation-donnees-freeda"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline text-primary hover:text-primary/80"
                  >
                    Lire la politique de confidentialité Free sur la conservation des données (fictif)
                  </a>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Message d'information */}
        <p className="text-xs text-center text-muted-foreground">
          Vos données sont protégées et ne seront utilisées que pour traiter votre demande.
        </p>
      </div>

      {/* Popup de confirmation d'appel */}
      <Dialog open={showCallConfirmation} onOpenChange={setShowCallConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Confirmation d'appel</DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-3 pt-2">
                <div>
                  Votre demande sera traitée par l'assistant vocal de Free. Il vous 
                  assistera et pourra vous renseigner sur vos factures, votre consommation, 
                  ou vous aider à résoudre un problème technique.
                </div>
                <div className="font-medium">
                  Souhaitez-vous continuer ?
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-row gap-3 justify-end">
            <Button
              variant="outline"
              onClick={handleCancelCall}
              className="flex-1 sm:flex-none"
            >
              Annuler
            </Button>
            <Button
              onClick={handleConfirmCall}
              className="flex-1 sm:flex-none bg-primary hover:bg-primary/90"
            >
              Continuer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Popup de confirmation WhatsApp */}
      <Dialog open={showWhatsAppConfirmation} onOpenChange={setShowWhatsAppConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-primary">
              <WhatsAppIcon className="w-6 h-6 text-primary" />
              Redirection WhatsApp
            </DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-3 pt-2">
                <div>
                  Vous allez être redirigé vers WhatsApp pour contacter l'assistant virtuel de Free. 
                  Il pourra vous aider avec vos questions.
                </div>
                <div className="font-medium">
                  Autorisez-vous cette redirection ?
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-row gap-3 justify-end">
            <Button
              variant="outline"
              onClick={handleCancelWhatsApp}
              className="flex-1 sm:flex-none"
            >
              Annuler
            </Button>
            <Button
              onClick={handleConfirmWhatsApp}
              className="flex-1 sm:flex-none bg-primary hover:bg-primary/90"
            >
              Oui, continuer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Popup de confirmation SMS */}
      <Dialog open={showSMSConfirmation} onOpenChange={setShowSMSConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-primary">
              <MessageSquare className="w-6 h-6 text-primary" />
              Redirection SMS
            </DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-3 pt-2">
                <div>
                  Vous allez être redirigé vers votre application de messagerie pour contacter l'assistant virtuel de Free. 
                  Il pourra vous aider avec vos questions.
                </div>
                <div className="font-medium">
                  Autorisez-vous cette redirection ?
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-row gap-3 justify-end">
            <Button
              variant="outline"
              onClick={handleCancelSMS}
              className="flex-1 sm:flex-none"
            >
              Annuler
            </Button>
            <Button
              onClick={handleConfirmSMS}
              className="flex-1 sm:flex-none bg-primary hover:bg-primary/90"
            >
              Oui, continuer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Popup de confirmation Email */}
      <Dialog open={showEmailConfirmation} onOpenChange={setShowEmailConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-primary">
              <Mail className="w-6 h-6 text-primary" />
              Redirection Email
            </DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-3 pt-2">
                <div>
                  Vous allez être redirigé vers votre client email pour envoyer une demande formelle au support Free. 
                  Un modèle d'email sera pré-rempli avec les informations nécessaires.
                </div>
                <div className="font-medium">
                  Autorisez-vous cette redirection ?
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-row gap-3 justify-end">
            <Button
              variant="outline"
              onClick={handleCancelEmail}
              className="flex-1 sm:flex-none"
            >
              Annuler
            </Button>
            <Button
              onClick={handleConfirmEmail}
              className="flex-1 sm:flex-none bg-primary hover:bg-primary/90"
            >
              Oui, continuer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}