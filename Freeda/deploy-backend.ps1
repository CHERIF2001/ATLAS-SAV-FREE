# Script de deploiement Backend Freeda (ECS + Docker)
# Build + Push ECR + Deploy CloudFormation

$env:AWS_PAGER = ""
$ErrorActionPreference = "Stop"
$region = "eu-west-3"
$environment = "production"
$projectName = "freeda"
$repoName = "$projectName-backend"
$stackName = "$projectName-ecs-$environment"

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "  DEPLOIEMENT BACKEND FREEDA (ECS)" -ForegroundColor Magenta
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ""

# ==================================================
# 1. ECR & Docker
# ==================================================
Write-Host "[1/4] Preparation Docker & ECR..." -ForegroundColor Cyan

# Recuperer l'Account ID
$accountId = aws sts get-caller-identity --query Account --output text
Write-Host "  AWS Account: $accountId" -ForegroundColor Gray

# Creer le repo ECR si necessaire
try {
    aws ecr describe-repositories --repository-names $repoName --region $region 2>$null | Out-Null
}
catch {
    Write-Host "  Creation du repository ECR..." -ForegroundColor Yellow
    aws ecr create-repository --repository-name $repoName --region $region | Out-Null
}

$ecrUri = "$accountId.dkr.ecr.$region.amazonaws.com/$repoName"
Write-Host "  ECR URI: $ecrUri" -ForegroundColor Gray

# Login ECR
Write-Host "  Login ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin "$accountId.dkr.ecr.$region.amazonaws.com"

# Build Docker
Write-Host "  Build de l'image Docker..." -ForegroundColor Yellow
if (Test-Path "backend") {
    Push-Location backend
    docker build -t "$repoName`:latest" .
    
    # Tag & Push
    $version = Get-Date -Format "yyyyMMdd-HHmmss"
    $imageUri = "$ecrUri`:$version"
    
    Write-Host "  Tag & Push vers ECR..." -ForegroundColor Yellow
    docker tag "$repoName`:latest" "$ecrUri`:latest"
    docker tag "$repoName`:latest" $imageUri
    
    docker push "$ecrUri`:latest"
    docker push $imageUri
    
    Pop-Location
    Write-Host "  [OK] Image poussee: $imageUri" -ForegroundColor Green
}
else {
    Write-Host "  [ERREUR] Dossier 'backend' introuvable" -ForegroundColor Red
    exit 1
}

# ==================================================
# 2. Configuration ECS
# ==================================================
Write-Host "[2/4] Configuration du deploiement..." -ForegroundColor Cyan

$paramsFile = "backend\infrastructure\parameters.json"
if (-not (Test-Path $paramsFile)) {
    Write-Host "  [ERREUR] $paramsFile introuvable" -ForegroundColor Red
    exit 1
}

# Mettre a jour l'image dans parameters.json
$json = Get-Content $paramsFile | ConvertFrom-Json
foreach ($param in $json) {
    if ($param.ParameterKey -eq "ContainerImage") {
        $param.ParameterValue = "$ecrUri`:latest"
    }
    if ($param.ParameterKey -eq "DynamoDBTableName") {
        $param.ParameterValue = "freeda-tickets-$environment"
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $paramsFile
Write-Host "  Parametres mis a jour avec la nouvelle image" -ForegroundColor Green

# ==================================================
# 3. Deploiement CloudFormation
# ==================================================
Write-Host "[3/4] Deploiement de la stack ECS..." -ForegroundColor Cyan

# Verifier si la stack existe
$stackExists = $false
try {
    aws cloudformation describe-stacks --stack-name $stackName --region $region 2>$null | Out-Null
    $stackExists = $true
}
catch {
    $stackExists = $false
}

if ($stackExists) {
    Write-Host "  Mise a jour de la stack ECS..." -ForegroundColor Yellow
    try {
        aws cloudformation update-stack `
            --stack-name $stackName `
            --template-body file://backend/infrastructure/ecs-fargate.yaml `
            --parameters file://$paramsFile `
            --capabilities CAPABILITY_IAM `
            --region $region 2>&1 | Out-Null
            
        Write-Host "  Mise a jour lancee, attente..." -ForegroundColor Cyan
        aws cloudformation wait stack-update-complete --stack-name $stackName --region $region
        Write-Host "  [OK] Stack mise a jour" -ForegroundColor Green
    }
    catch {
        if ($_.Exception.Message -match "No updates") {
            Write-Host "  [OK] Stack deja a jour (force deployment service...)" -ForegroundColor Green
            
            # Force update service pour prendre la nouvelle image
            $cluster = "freeda-cluster-$environment"
            $service = "freeda-service-$environment"
            aws ecs update-service --cluster $cluster --service $service --force-new-deployment --region $region | Out-Null
        }
        else {
            Write-Host "  [ERREUR] $_" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    Write-Host "  Creation de la stack ECS..." -ForegroundColor Yellow
    aws cloudformation create-stack `
        --stack-name $stackName `
        --template-body file://backend/infrastructure/ecs-fargate.yaml `
        --parameters file://$paramsFile `
        --capabilities CAPABILITY_IAM `
        --region $region

    Write-Host "  Creation lancee, attente (5-10 min)..." -ForegroundColor Cyan
    aws cloudformation wait stack-create-complete --stack-name $stackName --region $region
    Write-Host "  [OK] Stack creee" -ForegroundColor Green
}

# ==================================================
# 4. Resultats
# ==================================================
Write-Host "[4/4] Verification..." -ForegroundColor Cyan

$outputs = aws cloudformation describe-stacks --stack-name $stackName --region $region --query 'Stacks[0].Outputs' --output json | ConvertFrom-Json
$lbUrl = ($outputs | Where-Object { $_.OutputKey -eq "LoadBalancerDNS" }).OutputValue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "  BACKEND DEPLOYE AVEC SUCCES !" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL: http://$lbUrl" -ForegroundColor Cyan
Write-Host "Health Check: http://$lbUrl/health" -ForegroundColor Gray
Write-Host ""
Write-Host "Prochaine etape: Relancer le deploiement Frontend pour utiliser cette URL." -ForegroundColor Yellow
Write-Host ""
