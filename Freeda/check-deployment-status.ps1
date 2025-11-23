#!/usr/bin/env pwsh
# Script de vérification complète du déploiement Freeda sur AWS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ÉTAT DU DÉPLOIEMENT FREEDA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. CloudFormation Stacks
Write-Host "📦 CLOUDFORMATION STACKS" -ForegroundColor Yellow
Write-Host "------------------------"
$stacks = aws cloudformation list-stacks --region eu-west-3 --query "StackSummaries[?contains(StackName, 'freeda') && StackStatus != 'DELETE_COMPLETE'].[StackName,StackStatus]" --output text
if ($stacks) {
    $stacks -split "`n" | ForEach-Object {
        $parts = $_ -split "`t"
        $name = $parts[0]
        $status = $parts[1]
        $color = if ($status -match "COMPLETE") { "Green" } elseif ($status -match "PROGRESS") { "Yellow" } else { "Red" }
        Write-Host "  $name : " -NoNewline
        Write-Host $status -ForegroundColor $color
    }
}
else {
    Write-Host "  Aucune stack trouvée" -ForegroundColor Red
}
Write-Host ""

# 2. ECS Services
Write-Host "🐳 ECS SERVICES" -ForegroundColor Yellow
Write-Host "---------------"
try {
    $ecsStatus = aws ecs describe-services --cluster freeda-cluster-production --services freeda-service-production --region eu-west-3 --query 'services[0].[status,runningCount,desiredCount]' --output text 2>$null
    if ($ecsStatus) {
        $parts = $ecsStatus -split "`t"
        Write-Host "  Cluster: freeda-cluster-production"
        Write-Host "  Service: freeda-service-production"
        Write-Host "  Status: " -NoNewline
        Write-Host $parts[0] -ForegroundColor Green
        Write-Host "  Tasks: $($parts[1])/$($parts[2]) running"
    }
    else {
        Write-Host "  Service non trouvé ou non déployé" -ForegroundColor Red
    }
}
catch {
    Write-Host "  Erreur lors de la récupération du statut ECS" -ForegroundColor Red
}
Write-Host ""

# 3. CloudFront Distribution
Write-Host "🌐 CLOUDFRONT DISTRIBUTION" -ForegroundColor Yellow
Write-Host "--------------------------"
try {
    $cfStatus = aws cloudfront get-distribution --id EBGADJZTA473I --query 'Distribution.[Status,DomainName]' --output text 2>$null
    if ($cfStatus) {
        $parts = $cfStatus -split "`t"
        Write-Host "  Distribution ID: EBGADJZTA473I"
        Write-Host "  Status: " -NoNewline
        Write-Host $parts[0] -ForegroundColor Green
        Write-Host "  URL: https://$($parts[1])"
    }
}
catch {
    Write-Host "  Distribution non trouvée" -ForegroundColor Red
}
Write-Host ""

# 4. Dernière invalidation CloudFront
Write-Host "🔄 INVALIDATION CLOUDFRONT" -ForegroundColor Yellow
Write-Host "--------------------------"
try {
    $invalidations = aws cloudfront list-invalidations --distribution-id EBGADJZTA473I --query "InvalidationList.Items[0].[Id,Status,CreateTime]" --output text 2>$null
    if ($invalidations) {
        $parts = $invalidations -split "`t"
        Write-Host "  Dernière invalidation: $($parts[0])"
        Write-Host "  Status: " -NoNewline
        $color = if ($parts[1] -eq "Completed") { "Green" } else { "Yellow" }
        Write-Host $parts[1] -ForegroundColor $color
        Write-Host "  Créée le: $($parts[2])"
    }
}
catch {
    Write-Host "  Aucune invalidation trouvée" -ForegroundColor Gray
}
Write-Host ""

# 5. ALB (Application Load Balancer)
Write-Host "⚖️  APPLICATION LOAD BALANCER" -ForegroundColor Yellow
Write-Host "-----------------------------"
try {
    $albInfo = aws elbv2 describe-load-balancers --region eu-west-3 --query "LoadBalancers[?contains(LoadBalancerName, 'freeda')].[LoadBalancerName,DNSName,State.Code]" --output text 2>$null
    if ($albInfo) {
        $parts = $albInfo -split "`t"
        Write-Host "  Nom: $($parts[0])"
        Write-Host "  DNS: $($parts[1])"
        Write-Host "  État: " -NoNewline
        $color = if ($parts[2] -eq "active") { "Green" } else { "Yellow" }
        Write-Host $parts[2] -ForegroundColor $color
    }
}
catch {
    Write-Host "  ALB non trouvé" -ForegroundColor Red
}
Write-Host ""

# 6. S3 Bucket (Frontend)
Write-Host "🪣 S3 BUCKET (Frontend)" -ForegroundColor Yellow
Write-Host "-----------------------"
try {
    $bucketName = "freeda-frontend-production-717153733153"
    $bucketExists = aws s3 ls s3://$bucketName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Bucket: $bucketName"
        Write-Host "  Status: " -NoNewline
        Write-Host "Actif" -ForegroundColor Green
        
        # Dernier fichier uploadé
        $lastFile = aws s3 ls s3://$bucketName/assets/ --recursive | Sort-Object | Select-Object -Last 1
        if ($lastFile) {
            Write-Host "  Dernier déploiement: $($lastFile.Substring(0, 19))"
        }
    }
}
catch {
    Write-Host "  Bucket non trouvé" -ForegroundColor Red
}
Write-Host ""

# 7. DynamoDB Table
Write-Host "🗄️  DYNAMODB TABLE" -ForegroundColor Yellow
Write-Host "------------------"
try {
    $tableStatus = aws dynamodb describe-table --table-name freeda-tickets-production --region eu-west-3 --query 'Table.[TableStatus,ItemCount]' --output text 2>$null
    if ($tableStatus) {
        $parts = $tableStatus -split "`t"
        Write-Host "  Table: freeda-tickets-production"
        Write-Host "  Status: " -NoNewline
        Write-Host $parts[0] -ForegroundColor Green
        Write-Host "  Nombre d'items: $($parts[1])"
    }
}
catch {
    Write-Host "  Table non trouvée" -ForegroundColor Red
}
Write-Host ""

# 8. URLs importantes
Write-Host "🔗 URLS IMPORTANTES" -ForegroundColor Yellow
Write-Host "-------------------"
Write-Host "  Frontend (CloudFront): https://d7itckze71tqe.cloudfront.net"
Write-Host "  Backend API (ALB): http://freeda-alb-production-151117787.eu-west-3.elb.amazonaws.com"
Write-Host "  API Docs: https://d7itckze71tqe.cloudfront.net/docs"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   FIN DU RAPPORT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
