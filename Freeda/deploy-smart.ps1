#!/usr/bin/env pwsh
# Script de déploiement intelligent Freeda
# Vérifie, corrige et déploie automatiquement

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DÉPLOIEMENT INTELLIGENT FREEDA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# ÉTAPE 1 : VÉRIFICATIONS PRÉ-DÉPLOIEMENT
# ============================================
Write-Host "📋 ÉTAPE 1/6 : Vérifications pré-déploiement" -ForegroundColor Yellow
Write-Host "--------------------------------------------"

# Vérifier .env.production
Write-Host "  Vérification de .env.production..."
$envContent = Get-Content ".env.production" -Raw

if ($envContent -match "http://freeda-alb") {
    Write-Host "  ❌ .env.production contient l'ancienne URL ALB" -ForegroundColor Red
    Write-Host "  🔧 Correction automatique..." -ForegroundColor Yellow
    
    @"
VITE_API_URL=https://d7itckze71tqe.cloudfront.net
VITE_WS_URL=wss://d7itckze71tqe.cloudfront.net
VITE_ENVIRONMENT=production
"@ | Set-Content -Path ".env.production" -Encoding UTF8 -Force
    
    Write-Host "  ✅ .env.production corrigé" -ForegroundColor Green
}
elseif ($envContent -match "https://d7itckze71tqe.cloudfront.net") {
    Write-Host "  ✅ .env.production OK (CloudFront HTTPS)" -ForegroundColor Green
}
else {
    Write-Host "  ⚠️  .env.production a un format inattendu" -ForegroundColor Yellow
}

# Vérifier que les dépendances sont installées
Write-Host "  Vérification des dépendances..."
if (-not (Test-Path "node_modules")) {
    Write-Host "  ❌ node_modules manquant" -ForegroundColor Red
    Write-Host "  🔧 Installation des dépendances..." -ForegroundColor Yellow
    npm install
    Write-Host "  ✅ Dépendances installées" -ForegroundColor Green
}
else {
    Write-Host "  ✅ Dépendances OK" -ForegroundColor Green
}

Write-Host ""

# ============================================
# ÉTAPE 2 : BUILD
# ============================================
Write-Host "🔨 ÉTAPE 2/6 : Build du frontend" -ForegroundColor Yellow
Write-Host "--------------------------------"

Write-Host "  Construction du projet..."
$buildOutput = npm run build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erreur lors du build" -ForegroundColor Red
    Write-Host $buildOutput
    exit 1
}

# Extraire le nom du fichier JS généré
$jsFile = $buildOutput | Select-String -Pattern "index-([A-Za-z0-9]+)\.js" | ForEach-Object { $_.Matches.Value }
Write-Host "  ✅ Build réussi : $jsFile" -ForegroundColor Green
Write-Host ""

# ============================================
# ÉTAPE 3 : VÉRIFICATION POST-BUILD
# ============================================
Write-Host "🔍 ÉTAPE 3/6 : Vérification du build" -ForegroundColor Yellow
Write-Host "-------------------------------------"

# Vérifier que le fichier JS contient la bonne URL
$builtJsPath = "build/assets/$jsFile"
if (Test-Path $builtJsPath) {
    $jsContent = Get-Content $builtJsPath -Raw
    
    if ($jsContent -match "d7itckze71tqe\.cloudfront\.net") {
        Write-Host "  ✅ Le build contient l'URL CloudFront" -ForegroundColor Green
    }
    elseif ($jsContent -match "freeda-alb-production") {
        Write-Host "  ❌ ERREUR : Le build contient encore l'URL ALB !" -ForegroundColor Red
        Write-Host "  Le fichier .env.production n'a pas été pris en compte." -ForegroundColor Red
        Write-Host "  Relancez le script." -ForegroundColor Yellow
        exit 1
    }
    else {
        Write-Host "  ⚠️  Impossible de vérifier l'URL dans le build" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  ⚠️  Fichier JS non trouvé pour vérification" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# ÉTAPE 4 : DÉPLOIEMENT S3
# ============================================
Write-Host "☁️  ÉTAPE 4/6 : Déploiement sur S3" -ForegroundColor Yellow
Write-Host "----------------------------------"

# Récupérer les infos CloudFormation
$bucketName = aws cloudformation describe-stacks --stack-name freeda-frontend-production --region eu-west-3 --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text
$distId = aws cloudformation describe-stacks --stack-name freeda-frontend-production --region eu-west-3 --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" --output text

Write-Host "  Bucket S3 : $bucketName"
Write-Host "  Distribution CloudFront : $distId"

# Upload vers S3
Write-Host "  Upload des fichiers..."
aws s3 sync build/ s3://$bucketName/ --delete --cache-control "public,max-age=31536000,immutable" --exclude "index.html"
aws s3 cp build/index.html s3://$bucketName/index.html --cache-control "public,max-age=0,must-revalidate"

Write-Host "  ✅ Fichiers uploadés sur S3" -ForegroundColor Green
Write-Host ""

# ============================================
# ÉTAPE 5 : INVALIDATION CLOUDFRONT
# ============================================
Write-Host "🔄 ÉTAPE 5/6 : Invalidation CloudFront" -ForegroundColor Yellow
Write-Host "---------------------------------------"

Write-Host "  Création de l'invalidation..."
$invalidationId = (aws cloudfront create-invalidation --distribution-id $distId --paths "/*" --query "Invalidation.Id" --output text)
Write-Host "  Invalidation ID : $invalidationId"

Write-Host "  Attente de la fin de l'invalidation..."
$maxWait = 180 # 3 minutes max
$waited = 0
$interval = 10

while ($waited -lt $maxWait) {
    $status = aws cloudfront get-invalidation --distribution-id $distId --id $invalidationId --query "Invalidation.Status" --output text
    
    if ($status -eq "Completed") {
        Write-Host "  ✅ Invalidation terminée" -ForegroundColor Green
        break
    }
    
    Write-Host "  ⏳ Status: $status (attente ${waited}s/${maxWait}s)" -ForegroundColor Yellow
    Start-Sleep -Seconds $interval
    $waited += $interval
}

if ($waited -ge $maxWait) {
    Write-Host "  ⚠️  Timeout : l'invalidation prend plus de temps que prévu" -ForegroundColor Yellow
    Write-Host "  Le déploiement continuera en arrière-plan" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# ÉTAPE 6 : TESTS POST-DÉPLOIEMENT
# ============================================
Write-Host "🧪 ÉTAPE 6/6 : Tests post-déploiement" -ForegroundColor Yellow
Write-Host "--------------------------------------"

$cfUrl = "https://d7itckze71tqe.cloudfront.net"

# Test 1 : Vérifier que le bon fichier JS est servi
Write-Host "  Test 1 : Vérification du fichier JS servi..."
Start-Sleep -Seconds 5 # Attendre un peu pour la propagation
$indexHtml = Invoke-WebRequest -Uri "$cfUrl/index.html" -UseBasicParsing
if ($indexHtml.Content -match "index-AGnDm1d0\.js") {
    Write-Host "  ✅ Le bon fichier JS est servi" -ForegroundColor Green
}
else {
    Write-Host "  ⚠️  Le fichier JS servi pourrait être en cache" -ForegroundColor Yellow
}

# Test 2 : Test de l'API
Write-Host "  Test 2 : Test de l'API backend..."
try {
    $body = @{ initial_message = "Test automatique de déploiement" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$cfUrl/public/tickets/" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "  ✅ API fonctionne (Ticket: $($response.ticket_id))" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ API ne répond pas : $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3 : Test WebSocket
Write-Host "  Test 3 : Test WebSocket..."
try {
    $socket = New-Object System.Net.WebSockets.ClientWebSocket
    $cts = New-Object System.Threading.CancellationTokenSource
    $cts.CancelAfter(5000)
    $uri = New-Object System.Uri("wss://d7itckze71tqe.cloudfront.net/ws/test-id")
    $socket.ConnectAsync($uri, $cts.Token).Wait()
    
    if ($socket.State -eq 'Open') {
        Write-Host "  ✅ WebSocket fonctionne" -ForegroundColor Green
        $socket.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Test", $cts.Token).Wait()
    }
    else {
        Write-Host "  ⚠️  WebSocket état : $($socket.State)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ⚠️  WebSocket : $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# RAPPORT FINAL
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DÉPLOIEMENT TERMINÉ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 URL de l'application :" -ForegroundColor Green
Write-Host "   $cfUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Prochaines étapes :" -ForegroundColor Yellow
Write-Host "   1. Testez dans un navigateur en navigation privée"
Write-Host "   2. Vérifiez que tous les messages s'affichent"
Write-Host "   3. Testez la persistance (F5 pour rafraîchir)"
Write-Host ""
Write-Host "🔧 En cas de problème :" -ForegroundColor Yellow
Write-Host "   - Videz le cache du navigateur (Ctrl+Shift+Delete)"
Write-Host "   - Utilisez un autre navigateur"
Write-Host "   - Relancez ce script : .\deploy-smart.ps1"
Write-Host ""
