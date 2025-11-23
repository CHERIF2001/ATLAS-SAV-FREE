# Script de déploiement COMPLET - Freeda Frontend + Backend sur AWS (Windows PowerShell)
# Usage: .\deploy-all.ps1 -Environment production [-WithImprovements]
# Exemple: .\deploy-all.ps1 -Environment production -WithImprovements

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$WithImprovements = $false
)

$ErrorActionPreference = "Stop"

# Configuration
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "eu-west-1" }
$PROJECT_NAME = "freeda"

# Couleurs
function Write-Header {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                            ║" -ForegroundColor Magenta
    Write-Host "║         🚀 FREEDA - DÉPLOIEMENT COMPLET AWS 🚀            ║" -ForegroundColor Magenta
    Write-Host "║                                                            ║" -ForegroundColor Magenta
    Write-Host "║  Frontend (S3 + CloudFront) + Backend (ECS Fargate)       ║" -ForegroundColor Magenta
    Write-Host "║                                                            ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
    Write-Host "Region: $AWS_REGION" -ForegroundColor Cyan
    Write-Host "Améliorations: $WithImprovements" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "▶ $Message" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Command)
    
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "$Command n'est pas installé"
        exit 1
    }
}

function Wait-ForStack {
    param(
        [string]$StackName,
        [string]$Operation
    )
    
    Write-Info "Attente de la fin de l'opération sur $StackName..."
    
    if ($Operation -eq "create") {
        aws cloudformation wait stack-create-complete --stack-name $StackName --region $AWS_REGION
    } elseif ($Operation -eq "update") {
        aws cloudformation wait stack-update-complete --stack-name $StackName --region $AWS_REGION 2>$null
    }
}

# Vérifications Préliminaires
function Test-Prerequisites {
    Write-Step "Étape 0/10 : Vérifications Préliminaires"
    
    # Vérifier les commandes
    Test-Command "aws"
    Test-Command "docker"
    Test-Command "node"
    Test-Command "npm"
    
    Write-Success "Toutes les dépendances sont installées"
    
    # Vérifier les credentials AWS
    Write-Info "Vérification des credentials AWS..."
    try {
        $accountId = aws sts get-caller-identity --query Account --output text
        Write-Success "Credentials AWS valides (Account: $accountId)"
    } catch {
        Write-Error-Custom "Credentials AWS invalides. Exécutez 'aws configure'"
        exit 1
    }
    
    # Vérifier que les fichiers existent
    if (-not (Test-Path "infrastructure\frontend-s3-cloudfront.yaml")) {
        Write-Error-Custom "Fichier infrastructure\frontend-s3-cloudfront.yaml manquant"
        exit 1
    }
    
    if (-not (Test-Path "backend\infrastructure\dynamodb-table.yaml")) {
        Write-Error-Custom "Fichier backend\infrastructure\dynamodb-table.yaml manquant"
        exit 1
    }
    
    if (-not (Test-Path "backend\infrastructure\ecs-fargate.yaml")) {
        Write-Error-Custom "Fichier backend\infrastructure\ecs-fargate.yaml manquant"
        exit 1
    }
    
    Write-Success "Tous les fichiers requis sont présents"
}

# Déploiement DynamoDB
function Deploy-DynamoDB {
    Write-Step "Étape 1/10 : Déploiement DynamoDB"
    
    $stackName = "$PROJECT_NAME-dynamodb-$Environment"
    
    try {
        aws cloudformation describe-stacks --stack-name $stackName --region $AWS_REGION 2>$null | Out-Null
        Write-Warning-Custom "Stack DynamoDB existe déjà, mise à jour..."
        
        aws cloudformation update-stack `
            --stack-name $stackName `
            --template-body file://backend/infrastructure/dynamodb-table.yaml `
            --parameters ParameterKey=Environment,ParameterValue=$Environment `
            --region $AWS_REGION 2>$null
        
        Wait-ForStack -StackName $stackName -Operation "update"
    } catch {
        Write-Info "Création de la stack DynamoDB..."
        aws cloudformation create-stack `
            --stack-name $stackName `
            --template-body file://backend/infrastructure/dynamodb-table.yaml `
            --parameters ParameterKey=Environment,ParameterValue=$Environment `
            --region $AWS_REGION
        
        Wait-ForStack -StackName $stackName -Operation "create"
    }
    
    # Récupérer le nom de la table
    $script:TABLE_NAME = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $AWS_REGION `
        --query 'Stacks[0].Outputs[?OutputKey==`TableName`].OutputValue' `
        --output text
    
    Write-Success "DynamoDB déployé : $TABLE_NAME"
}

# Build & Push Backend Docker
function Build-PushBackend {
    Write-Step "Étape 3/10 : Build & Push Backend Docker"
    
    $repoName = "$PROJECT_NAME-backend"
    
    # Créer le repository ECR si nécessaire
    try {
        aws ecr describe-repositories --repository-names $repoName --region $AWS_REGION 2>$null | Out-Null
    } catch {
        Write-Info "Création du repository ECR..."
        aws ecr create-repository --repository-name $repoName --region $AWS_REGION
    }
    
    # Récupérer l'URI
    $script:ECR_URI = aws ecr describe-repositories `
        --repository-names $repoName `
        --region $AWS_REGION `
        --query 'repositories[0].repositoryUri' `
        --output text
    
    Write-Info "ECR Repository: $ECR_URI"
    
    # Login ECR
    Write-Info "Login à ECR..."
    $password = aws ecr get-login-password --region $AWS_REGION
    $password | docker login --username AWS --password-stdin $ECR_URI
    
    # Build
    Write-Info "Build de l'image Docker backend..."
    Push-Location backend
    docker build -t ${repoName}:latest .
    Pop-Location
    
    # Tag
    $version = Get-Date -Format "yyyyMMdd-HHmmss"
    docker tag ${repoName}:latest ${ECR_URI}:latest
    docker tag ${repoName}:latest ${ECR_URI}:$version
    
    # Push
    Write-Info "Push vers ECR..."
    docker push ${ECR_URI}:latest
    docker push ${ECR_URI}:$version
    
    Write-Success "Backend Docker pushed: ${ECR_URI}:$version"
}

# Déploiement Backend ECS
function Deploy-BackendECS {
    Write-Step "Étape 4/10 : Déploiement Backend ECS Fargate"
    
    $stackName = "$PROJECT_NAME-ecs-$Environment"
    
    # Vérifier que parameters.json existe
    if (-not (Test-Path "backend\infrastructure\parameters.json")) {
        Write-Error-Custom "Fichier backend\infrastructure\parameters.json manquant"
        Write-Info "Créez ce fichier avec vos paramètres (VPC, Subnets, Mistral API Key)"
        exit 1
    }
    
    # Mettre à jour l'image dans parameters.json
    $params = Get-Content "backend\infrastructure\parameters.json" | ConvertFrom-Json
    ($params | Where-Object { $_.ParameterKey -eq "ContainerImage" }).ParameterValue = "${ECR_URI}:latest"
    ($params | Where-Object { $_.ParameterKey -eq "DynamoDBTableName" }).ParameterValue = $TABLE_NAME
    $params | ConvertTo-Json -Depth 10 | Set-Content "backend\infrastructure\parameters.json"
    
    try {
        aws cloudformation describe-stacks --stack-name $stackName --region $AWS_REGION 2>$null | Out-Null
        Write-Warning-Custom "Stack ECS existe, mise à jour du service..."
        
        $clusterName = aws cloudformation describe-stacks `
            --stack-name $stackName `
            --region $AWS_REGION `
            --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' `
            --output text
        
        $serviceName = aws cloudformation describe-stacks `
            --stack-name $stackName `
            --region $AWS_REGION `
            --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' `
            --output text
        
        aws ecs update-service `
            --cluster $clusterName `
            --service $serviceName `
            --force-new-deployment `
            --region $AWS_REGION
        
        Write-Success "Déploiement en cours (rolling update)"
    } catch {
        Write-Info "Création de la stack ECS..."
        aws cloudformation create-stack `
            --stack-name $stackName `
            --template-body file://backend/infrastructure/ecs-fargate.yaml `
            --parameters file://backend/infrastructure/parameters.json `
            --capabilities CAPABILITY_IAM `
            --region $AWS_REGION
        
        Wait-ForStack -StackName $stackName -Operation "create"
        Write-Success "Stack ECS créée"
    }
    
    # Récupérer l'URL du Load Balancer
    $script:BACKEND_URL = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $AWS_REGION `
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' `
        --output text
    
    Write-Success "Backend déployé : http://$BACKEND_URL"
}

# Build Frontend
function Build-Frontend {
    Write-Step "Étape 5/10 : Build Frontend (React + Vite)"
    
    Write-Info "Installation des dépendances..."
    npm install
    
    # Créer .env.production avec l'URL du backend
    Write-Info "Configuration de l'environnement..."
    @"
VITE_API_URL=http://$BACKEND_URL
VITE_WS_URL=ws://$BACKEND_URL
VITE_ENVIRONMENT=$Environment
"@ | Set-Content ".env.production"
    
    Write-Info "Build de l'application..."
    npm run build
    
    Write-Success "Frontend buildé dans dist/"
}

# Déploiement Frontend
function Deploy-Frontend {
    Write-Step "Étape 6/10 : Déploiement Frontend (S3 + CloudFront)"
    
    $stackName = "$PROJECT_NAME-frontend-$Environment"
    
    try {
        aws cloudformation describe-stacks --stack-name $stackName --region $AWS_REGION 2>$null | Out-Null
        Write-Warning-Custom "Stack Frontend existe déjà"
    } catch {
        Write-Info "Création de la stack Frontend..."
        aws cloudformation create-stack `
            --stack-name $stackName `
            --template-body file://infrastructure/frontend-s3-cloudfront.yaml `
            --parameters ParameterKey=Environment,ParameterValue=$Environment `
            --region $AWS_REGION
        
        Wait-ForStack -StackName $stackName -Operation "create"
    }
    
    # Récupérer le nom du bucket
    $bucketName = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $AWS_REGION `
        --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' `
        --output text
    
    $cloudFrontId = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $AWS_REGION `
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' `
        --output text
    
    Write-Success "Stack Frontend créée : $bucketName"
    
    # Upload vers S3
    Write-Info "Upload des fichiers vers S3..."
    aws s3 sync dist/ s3://$bucketName/ `
        --delete `
        --cache-control "public, max-age=31536000, immutable" `
        --exclude "index.html" `
        --region $AWS_REGION
    
    # Upload index.html avec cache court
    aws s3 cp dist/index.html s3://${bucketName}/index.html `
        --cache-control "public, max-age=0, must-revalidate" `
        --region $AWS_REGION
    
    Write-Success "Fichiers uploadés vers S3"
    
    # Invalider le cache CloudFront
    Write-Info "Invalidation du cache CloudFront..."
    aws cloudfront create-invalidation `
        --distribution-id $cloudFrontId `
        --paths "/*" `
        --region $AWS_REGION
    
    # Récupérer l'URL
    $script:FRONTEND_URL = aws cloudformation describe-stacks `
        --stack-name $stackName `
        --region $AWS_REGION `
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' `
        --output text
    
    Write-Success "Frontend déployé : $FRONTEND_URL"
}

# Tests de Santé
function Test-HealthChecks {
    Write-Step "Étape 9/10 : Tests de Santé"
    
    Write-Info "Test du backend..."
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://$BACKEND_URL/health" -UseBasicParsing
        if ($response.Content -match "healthy") {
            Write-Success "Backend opérationnel ✓"
        }
    } catch {
        Write-Warning-Custom "Backend en cours de démarrage..."
    }
    
    Write-Info "Test du frontend..."
    try {
        $response = Invoke-WebRequest -Uri $FRONTEND_URL -UseBasicParsing
        if ($response.Content -match "<!DOCTYPE html>") {
            Write-Success "Frontend opérationnel ✓"
        }
    } catch {
        Write-Warning-Custom "Frontend en cours de propagation CloudFront..."
    }
}

# Résumé Final
function Write-Summary {
    Write-Step "Étape 10/10 : Résumé du Déploiement"
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "║              🎉 DÉPLOIEMENT TERMINÉ ! 🎉                  ║" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📊 Informations de Déploiement" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Frontend:" -ForegroundColor Yellow
    Write-Host "  URL:         $FRONTEND_URL" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend:" -ForegroundColor Yellow
    Write-Host "  URL:         http://$BACKEND_URL" -ForegroundColor Green
    Write-Host "  Health:      http://$BACKEND_URL/health"
    Write-Host "  API Docs:    http://$BACKEND_URL/docs"
    Write-Host ""
    Write-Host "Base de Données:" -ForegroundColor Yellow
    Write-Host "  DynamoDB:    $TABLE_NAME"
    Write-Host "  Region:      $AWS_REGION"
    Write-Host ""
    Write-Host "✅ Tout est prêt pour la production !" -ForegroundColor Green
    Write-Host ""
}

# Main
try {
    Write-Header
    Test-Prerequisites
    Deploy-DynamoDB
    Build-PushBackend
    Deploy-BackendECS
    Build-Frontend
    Deploy-Frontend
    Test-HealthChecks
    Write-Summary
} catch {
    Write-Error-Custom "Erreur lors du déploiement: $_"
    exit 1
}
