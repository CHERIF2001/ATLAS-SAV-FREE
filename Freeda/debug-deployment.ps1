#!/usr/bin/env pwsh
# Script de debug intelligent Freeda
# Diagnostique automatiquement les problèmes courants

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DIAGNOSTIC FREEDA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$warnings = @()

# ============================================
# 1. CONFIGURATION LOCALE
# ============================================
Write-Host "📁 Configuration locale" -ForegroundColor Yellow
Write-Host "-----------------------"

# Vérifier .env.production
if (Test-Path ".env.production") {
    $envProd = Get-Content ".env.production" -Raw
    Write-Host "  .env.production :" -ForegroundColor Cyan
    Write-Host "    $($envProd -replace "`n", "`n    ")"
    
    if ($envProd -match "http://freeda-alb") {
        $issues += "❌ .env.production contient l'URL ALB HTTP au lieu de CloudFront HTTPS"
    }
    elseif ($envProd -match "https://d7itckze71tqe.cloudfront.net") {
        Write-Host "  ✅ .env.production OK" -ForegroundColor Green
    }
    else {
        $warnings += "⚠️  .env.production a un format inattendu"
    }
}
else {
    $issues += "❌ .env.production manquant"
}

# Vérifier .env.local
if (Test-Path ".env.local") {
    $envLocal = Get-Content ".env.local" -Raw
    Write-Host "  .env.local :" -ForegroundColor Cyan
    Write-Host "    $($envLocal -replace "`n", "`n    ")"
    Write-Host "  ✅ .env.local existe" -ForegroundColor Green
}
else {
    $warnings += "⚠️  .env.local manquant (optionnel)"
}

Write-Host ""

# ============================================
# 2. BUILD
# ============================================
Write-Host "🔨 Build" -ForegroundColor Yellow
Write-Host "--------"

if (Test-Path "build") {
    $buildFiles = Get-ChildItem "build/assets" -Filter "index-*.js" | Select-Object -First 1
    if ($buildFiles) {
        Write-Host "  Dernier build : $($buildFiles.Name)" -ForegroundColor Cyan
        
        # Vérifier le contenu
        $jsContent = Get-Content $buildFiles.FullName -Raw
        if ($jsContent -match "d7itckze71tqe\.cloudfront\.net") {
            Write-Host "  ✅ Le build contient l'URL CloudFront" -ForegroundColor Green
        }
        elseif ($jsContent -match "freeda-alb-production") {
            $issues += "❌ Le build contient l'URL ALB au lieu de CloudFront"
        }
        else {
            $warnings += "⚠️  Impossible de détecter l'URL dans le build"
        }
    }
    else {
        $warnings += "⚠️  Aucun fichier JS trouvé dans build/assets"
    }
}
else {
    $warnings += "⚠️  Dossier build/ manquant (lancez npm run build)"
}

Write-Host ""

# ============================================
# 3. AWS - CloudFormation
# ============================================
Write-Host "☁️  AWS - CloudFormation" -ForegroundColor Yellow
Write-Host "------------------------"

try {
    $stackStatus = aws cloudformation describe-stacks --stack-name freeda-frontend-production --region eu-west-3 --query "Stacks[0].StackStatus" --output text 2>$null
    
    if ($stackStatus) {
        Write-Host "  Stack Status : $stackStatus" -ForegroundColor Cyan
        if ($stackStatus -match "COMPLETE") {
            Write-Host "  ✅ Stack CloudFormation OK" -ForegroundColor Green
        }
        else {
            $warnings += "⚠️  Stack CloudFormation en état : $stackStatus"
        }
    }
    else {
        $issues += "❌ Stack CloudFormation introuvable"
    }
}
catch {
    $issues += "❌ Impossible de contacter AWS CloudFormation"
}

Write-Host ""

# ============================================
# 4. AWS - S3
# ============================================
Write-Host "🪣 AWS - S3" -ForegroundColor Yellow
Write-Host "-----------"

try {
    $bucketName = "freeda-frontend-production-717153733153"
    $s3Files = aws s3 ls "s3://$bucketName/assets/" --recursive 2>$null | Select-Object -Last 3
    
    if ($s3Files) {
        Write-Host "  Derniers fichiers sur S3 :" -ForegroundColor Cyan
        $s3Files | ForEach-Object { Write-Host "    $_" }
        Write-Host "  ✅ Bucket S3 accessible" -ForegroundColor Green
    }
    else {
        $issues += "❌ Bucket S3 vide ou inaccessible"
    }
}
catch {
    $issues += "❌ Impossible d'accéder au bucket S3"
}

Write-Host ""

# ============================================
# 5. AWS - CloudFront
# ============================================
Write-Host "🌐 AWS - CloudFront" -ForegroundColor Yellow
Write-Host "-------------------"

try {
    $distId = "EBGADJZTA473I"
    $distStatus = aws cloudfront get-distribution --id $distId --query "Distribution.Status" --output text 2>$null
    
    if ($distStatus) {
        Write-Host "  Distribution Status : $distStatus" -ForegroundColor Cyan
        Write-Host "  ✅ CloudFront accessible" -ForegroundColor Green
        
        # Vérifier la dernière invalidation
        $lastInvalidation = aws cloudfront list-invalidations --distribution-id $distId --query "InvalidationList.Items[0].[Id,Status,CreateTime]" --output text 2>$null
        if ($lastInvalidation) {
            $parts = $lastInvalidation -split "`t"
            Write-Host "  Dernière invalidation :" -ForegroundColor Cyan
            Write-Host "    ID     : $($parts[0])"
            Write-Host "    Status : $($parts[1])"
            Write-Host "    Date   : $($parts[2])"
            
            if ($parts[1] -eq "Completed") {
                Write-Host "  ✅ Invalidation terminée" -ForegroundColor Green
            }
            else {
                $warnings += "⚠️  Invalidation en cours : $($parts[1])"
            }
        }
    }
    else {
        $issues += "❌ Distribution CloudFront introuvable"
    }
}
catch {
    $issues += "❌ Impossible d'accéder à CloudFront"
}

Write-Host ""

# ============================================
# 6. BACKEND API
# ============================================
Write-Host "🔌 Backend API" -ForegroundColor Yellow
Write-Host "--------------"

try {
    $body = @{ initial_message = "Test diagnostic" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "https://d7itckze71tqe.cloudfront.net/public/tickets/" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    
    Write-Host "  ✅ API fonctionne" -ForegroundColor Green
    Write-Host "  Ticket créé : $($response.ticket_id)" -ForegroundColor Cyan
}
catch {
    $issues += "❌ API ne répond pas : $($_.Exception.Message)"
}

Write-Host ""

# ============================================
# 7. ECS SERVICE
# ============================================
Write-Host "🐳 ECS Service" -ForegroundColor Yellow
Write-Host "--------------"

try {
    $ecsInfo = aws ecs describe-services --cluster freeda-cluster-production --services freeda-service-production --region eu-west-3 --query "services[0].[status,runningCount,desiredCount]" --output text 2>$null
    
    if ($ecsInfo) {
        $parts = $ecsInfo -split "`t"
        Write-Host "  Status : $($parts[0])" -ForegroundColor Cyan
        Write-Host "  Tasks  : $($parts[1])/$($parts[2]) running" -ForegroundColor Cyan
        
        if ($parts[0] -eq "ACTIVE" -and $parts[1] -eq $parts[2]) {
            Write-Host "  ✅ ECS Service OK" -ForegroundColor Green
        }
        else {
            $warnings += "⚠️  ECS Service : $($parts[1])/$($parts[2]) tasks actives"
        }
    }
    else {
        $issues += "❌ ECS Service introuvable"
    }
}
catch {
    $issues += "❌ Impossible d'accéder à ECS"
}

Write-Host ""

# ============================================
# RAPPORT FINAL
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RAPPORT DE DIAGNOSTIC" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ AUCUN PROBLÈME DÉTECTÉ" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tout semble fonctionner correctement !" -ForegroundColor Green
}
else {
    if ($issues.Count -gt 0) {
        Write-Host "❌ PROBLÈMES CRITIQUES :" -ForegroundColor Red
        $issues | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠️  AVERTISSEMENTS :" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        Write-Host ""
    }
    
    Write-Host "🔧 SOLUTIONS RECOMMANDÉES :" -ForegroundColor Cyan
    
    if ($issues -match ".env.production") {
        Write-Host "  1. Lancez : .\deploy-smart.ps1" -ForegroundColor Yellow
        Write-Host "     (corrigera automatiquement .env.production)"
    }
    
    if ($issues -match "build") {
        Write-Host "  2. Lancez : npm run build" -ForegroundColor Yellow
    }
    
    if ($issues -match "API") {
        Write-Host "  3. Vérifiez que le backend ECS est démarré" -ForegroundColor Yellow
    }
    
    if ($warnings -match "Invalidation") {
        Write-Host "  4. Attendez la fin de l'invalidation CloudFront" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
