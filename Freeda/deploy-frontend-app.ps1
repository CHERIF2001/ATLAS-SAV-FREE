# Script de deploiement complet Frontend Freeda - Version corrigee pour build/
# Build + Upload S3 + Invalidation CloudFront

$env:AWS_PAGER = ""
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "  DEPLOIEMENT COMPLET FRONTEND FREEDA" -ForegroundColor Magenta
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ""

$region = "eu-west-3"
$stackName = "freeda-frontend-production"
$buildDir = "build"  # Le dossier de build est 'build' et non 'dist'

# Recuperer les informations AWS
Write-Host "[1/5] Recuperation des informations CloudFormation..." -ForegroundColor Cyan

$outputs = aws cloudformation describe-stacks `
    --stack-name $stackName `
    --region $region `
    --query 'Stacks[0].Outputs' `
    --output json | ConvertFrom-Json

$bucketName = ($outputs | Where-Object { $_.OutputKey -eq "BucketName" }).OutputValue
$cloudFrontUrl = ($outputs | Where-Object { $_.OutputKey -eq "WebsiteURL" }).OutputValue
$distributionId = ($outputs | Where-Object { $_.OutputKey -eq "CloudFrontDistributionId" }).OutputValue

Write-Host "  Bucket S3: $bucketName" -ForegroundColor Green
Write-Host "  CloudFront URL: $cloudFrontUrl" -ForegroundColor Green
Write-Host "  Distribution ID: $distributionId" -ForegroundColor Green
Write-Host ""

# Recuperer l'URL du Backend
Write-Host "[2/5] Recuperation de l'URL du Backend ECS..." -ForegroundColor Cyan

try {
    $backendUrl = aws cloudformation describe-stacks `
        --stack-name "freeda-ecs-production" `
        --region $region `
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' `
        --output text 2>$null
    
    if ($backendUrl) {
        Write-Host "  Backend URL: http://$backendUrl" -ForegroundColor Green
    }
    else {
        Write-Host "  [WARN] Backend pas deploye, utilisation locale" -ForegroundColor Yellow
        $backendUrl = "localhost:8000"
    }
}
catch {
    Write-Host "  [WARN] Backend pas deploye, utilisation locale" -ForegroundColor Yellow
    $backendUrl = "localhost:8000"
}
Write-Host ""

# Configuration de l'environnement
Write-Host "[3/5] Configuration .env.production..." -ForegroundColor Cyan

$envContent = @"
VITE_API_URL=http://$backendUrl
VITE_WS_URL=ws://$backendUrl
VITE_ENVIRONMENT=production
"@

$envContent | Set-Content ".env.production"
Write-Host "  Fichier .env.production cree" -ForegroundColor Green
Write-Host ""

# Upload vers S3 (le build existe deja)
Write-Host "[4/5] Upload vers S3..." -ForegroundColor Cyan

if (-not (Test-Path $buildDir)) {
    Write-Host "  [ERREUR] Le dossier $buildDir/ n'existe pas" -ForegroundColor Red
    Write-Host "  Lancez 'npm run build' d'abord" -ForegroundColor Yellow
    exit 1
}

$fileCount = (Get-ChildItem -Path $buildDir -Recurse -File).Count
Write-Host "  $fileCount fichiers trouves dans $buildDir/" -ForegroundColor Cyan

Write-Host "  Upload des fichiers statiques..." -ForegroundColor Yellow

aws s3 sync $buildDir/ s3://$bucketName/ `
    --delete `
    --cache-control "public, max-age=31536000, immutable" `
    --exclude "index.html" `
    --region $region

Write-Host "  Upload de index.html..." -ForegroundColor Yellow

aws s3 cp $buildDir/index.html s3://$bucketName/index.html `
    --cache-control "public, max-age=0, must-revalidate" `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Upload termine!" -ForegroundColor Green
}
else {
    Write-Host "  [ERREUR] L'upload a echoue" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Invalidation CloudFront
Write-Host "[5/5] Invalidation du cache CloudFront..." -ForegroundColor Cyan

$invalidation = aws cloudfront create-invalidation `
    --distribution-id $distributionId `
    --paths "/*" `
    --region $region `
    --output json | ConvertFrom-Json

if ($invalidation) {
    $invalidationId = $invalidation.Invalidation.Id
    Write-Host "  [OK] Invalidation: $invalidationId" -ForegroundColor Green
    Write-Host "  Propagation: 2-5 minutes" -ForegroundColor Yellow
}
else {
    Write-Host "  [WARN] Invalidation echouee" -ForegroundColor Yellow
}
Write-Host ""

# Resume
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "  DEPLOIEMENT FRONTEND TERMINE !" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "URL: $cloudFrontUrl" -ForegroundColor White
Write-Host "Bucket: $bucketName" -ForegroundColor Cyan
Write-Host "Distribution: $distributionId" -ForegroundColor Cyan
Write-Host "Backend: http://$backendUrl" -ForegroundColor Cyan
Write-Host ""

if ($backendUrl -eq "localhost:8000") {
    Write-Host "[ATTENTION] Le backend n'est pas encore deploye!" -ForegroundColor Red
    Write-Host "Executez: .\deploy-all.ps1 -Environment production" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Le site sera accessible dans 2-5 minutes..." -ForegroundColor Yellow
Write-Host "===========================================================" -ForegroundColor Green
Write-Host ""
