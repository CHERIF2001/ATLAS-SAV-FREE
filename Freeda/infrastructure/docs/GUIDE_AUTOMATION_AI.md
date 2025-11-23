# 📘 GUIDE D’AUTOMATISATION POUR UNE IA DE GÉNÉRATION DE CODE

## 🎯 Objectif
Fournir à une IA de génération de code (ex. : Copilot, GPT‑4‑Code, Claude‑Code) toutes les informations nécessaires pour :
1. **Faire fonctionner le backend Freeda en production via un tunnel HTTPS gratuit (ngrok).**
2. **Mettre à jour le frontend afin qu’il utilise ce tunnel.**
3. **Re‑builder et redéployer le frontend sur CloudFront.**
4. **Obtenir un lien fonctionnel que les évaluateurs peuvent tester sans nom de domaine payant.**

Le tout doit être réalisé **sans écraser accidentellement du code existant** et en respectant les contraintes suivantes :
- Aucun fichier en dehors du répertoire `c:\Users\Yann LAVRY\Documents\GitHub\ATLAS-SAV-FREE\Freeda` ne doit être modifié.
- Les actions qui peuvent interrompre un processus en cours (ex. : `aws cloudformation update‑stack` qui tourne depuis 38 min) ne doivent pas être annulées.
- Tous les scripts PowerShell doivent être lancés **en arrière‑plan** afin de ne pas bloquer l’interpréteur.
- Les étapes doivent être **atomiques** : chaque commande doit vérifier son succès avant de passer à la suivante.

---

## 📂 Structure du projet (extraits pertinents)
```
Freeda/
├─ backend/                # FastAPI + Mistral AI
│   └─ main.py
├─ frontend/               # Vite + React (TS)
│   └─ vite.config.ts
├─ .env.production         # Variables d’environnement du frontend
├─ deploy‑frontend‑app.ps1  # Script qui synchronise le build S3 + invalide le cache CloudFront
├─ quick‑status.ps1        # Script d’état rapide (non utilisé dans la démo)
├─ infrastructure/
│   └─ frontend‑s3‑cloudfront.yaml   # CloudFormation du frontend
└─ ...
```

## 🔧 Prérequis (déjà installés dans le dépôt)
- **PowerShell 5+** (exécuté sous Windows).
- **Node.js ≥ 18** et **npm** (pour le build du frontend).
- **Python ≥ 3.11** et les dépendances du backend (`pip install -r requirements.txt`).
- **AWS CLI** configuré avec les credentials du compte où le stack CloudFormation existe.
- **ngrok** (exécutable `ngrok.exe` présent à la racine du projet – le script le télécharge s’il manque).

## 🛠️ Étapes détaillées (ordre strict)

### 1️⃣ Vérifier les prérequis
```powershell
# 1.1 Node & npm
node --version
npm --version
# 1.2 Python
python --version
# 1.3 AWS CLI
aws --version
# 1.4 ngrok (téléchargé si absent – déjà fait dans le repo)
if (-not (Test-Path "./ngrok.exe")) { iwr -Uri https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-windows-amd64.zip -OutFile ngrok.zip; Expand-Archive ngrok.zip -DestinationPath . }
```
> **Note** : chaque commande doit renvoyer un code 0. En cas d’erreur, abort + loguer le problème.

### 2️⃣ Arrêter d’éventuels tunnels ngrok déjà en cours
```powershell
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
```
> Cela garantit qu’on part d’un état propre et évite les conflits de ports.

### 3️⃣ Lancer un nouveau tunnel HTTPS vers le backend
```powershell
# Le backend écoute sur le port 8000 (ALB HTTP). Nous exposons ce port via ngrok.
$ngrok = Start-Process -FilePath "./ngrok.exe" -ArgumentList "http 8000 --log=stdout" -NoNewWindow -PassThru
# Attendre que l’API locale de ngrok soit disponible (≈ 10‑12 s)
Start-Sleep -Seconds 12
```
> **Pourquoi** : ngrok crée une URL publique HTTPS (ex : `https://abcd1234.ngrok.io`). Cette URL contourne la CSP de CloudFront qui n’autorise que HTTPS.

### 4️⃣ Récupérer l’URL publique du tunnel
```powershell
try {
    $info = Invoke-RestMethod -Uri http://127.0.0.1:4040/api/tunnels -ErrorAction Stop
    $publicUrl = $info.tunnels[0].public_url   # ex: https://abcd1234.ngrok.io
    Write-Host "🔗 Tunnel public URL: $publicUrl" -ForegroundColor Green
} catch {
    Write-Error "Impossible de récupérer l’URL du tunnel ngrok. Abandon."; exit 1
}
```
> **Fail‑fast** : si l’URL n’est pas récupérée, on arrête le script afin d’éviter d’écraser `.env.production` avec une valeur vide.

### 5️⃣ Mettre à jour le fichier `.env.production`
```powershell
$envFile = ".env.production"
# Remplacer l’ancienne URL HTTP du ALB par l’URL HTTPS du tunnel
(Get-Content $envFile) -replace 'http://freeda-alb-production-1511177887\.eu-west-3\.elb\.amazonaws\.com', $publicUrl |
    Set-Content $envFile
Write-Host "✅ .env.production mis à jour avec l’URL du tunnel" -ForegroundColor Green
```
> **Attention** : on ne touche qu’à la ligne contenant l’URL, aucune autre variable n’est modifiée.

### 6️⃣ Re‑builder le frontend (Vite)
```powershell
npm run build
if ($LASTEXITCODE -ne 0) { Write-Error "npm run build a échoué. Abandon."; exit 1 }
Write-Host "✅ Build du frontend terminé" -ForegroundColor Green
```
> Le build génère le dossier `dist/` qui sera synchronisé avec le bucket S3.

### 7️⃣ Redéployer le frontend sur CloudFront
```powershell
# Le script fourni synchronise le bucket S3 et invalide le cache CloudFront.
.\deploy-frontend-app.ps1
if ($LASTEXITCODE -ne 0) { Write-Error "deploy-frontend-app.ps1 a échoué. Abandon."; exit 1 }
Write-Host "✅ Frontend redéployé sur CloudFront" -ForegroundColor Green
```
> Le script utilise les paramètres du stack CloudFormation déjà existant ; il ne modifie pas la stack elle‑même.

### 8️⃣ Afficher le lien final à partager
```powershell
Write-Host "\n🌐 Lien de démonstration à partager avec les évaluateurs :" -ForegroundColor Cyan
Write-Host "   https://d7itckze71tqe.cloudfront.net" -ForegroundColor White
Write-Host "\n⚠️ Gardez le terminal ngrok ouvert tant que vous voulez que le backend reste accessible via le tunnel.\n" -ForegroundColor Yellow
```
> Le lien CloudFront reste identique ; le backend est désormais reachable via le tunnel HTTPS.

### 9️⃣ Nettoyage (optionnel)
```powershell
# Si vous voulez arrêter le tunnel après la démo :
$ngrok | Stop-Process -Force
Write-Host "✅ Tunnel ngrok arrêté" -ForegroundColor Green
```
> Cela libère le port 8000 et évite les processus orphelins.

---

## 📋 Résumé des points critiques pour l’IA
1. **Ne jamais modifier le stack CloudFormation** tant que la mise à jour en cours (`aws cloudformation update‑stack …`) n’est pas terminée ; le script ne l’interfère pas.
2. **Toujours vérifier le code de sortie** (`$LASTEXITCODE`) après chaque commande ; en cas d’erreur, loguer et `exit 1`.
3. **Utiliser `Start-Process -PassThru`** pour garder une référence au processus ngrok afin de le stopper proprement.
4. **Attendre** (12 s) avant de lire l’API locale de ngrok ; sinon `NGROK_NOT_RUNNING` sera retourné.
5. **Mettre à jour uniquement la ligne d’URL** dans `.env.production` ; ne pas toucher aux autres variables.
6. **Le build et le déploiement** sont séparés : `npm run build` → `deploy‑frontend‑app.ps1`. Aucun fichier source du projet n’est écrasé.
7. **Le lien final** reste le même (`https://d7itckze71tqe.cloudfront.net`). C’est le CDN qui sert le frontend; le backend est redirigé via le tunnel.
8. **Conserver le processus ngrok** tant que la démo doit rester accessible ; sinon le backend redeviendra inaccessible.

---

## 📦 Fichier généré
Le contenu ci‑dessus a été sauvegardé dans le fichier :
```
c:\Users\Yann LAVRY\Documents\GitHub\ATLAS-SAV-FREE\Freeda\GUIDE_AUTOMATION_AI.md
```
Ce document peut être lu par n’importe quelle IA de génération de code pour reproduire la démo sans risque de crash ou de corruption du code.

---

**Bonne démo !** 🚀
