# Script pour recuperer automatiquement votre configuration AWS
# Usage: .\get-aws-config.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Recuperation de votre configuration AWS..." -ForegroundColor Cyan
Write-Host ""

# Region
$region = if ($env:AWS_REGION) { $env:AWS_REGION } else { "eu-west-3" }
Write-Host "Region: $region" -ForegroundColor Green
Write-Host ""

# Account ID
try {
  $accountId = aws sts get-caller-identity --query Account --output text
  Write-Host "Account ID: $accountId" -ForegroundColor Green
}
catch {
  Write-Host "Erreur: Impossible de recuperer l'Account ID" -ForegroundColor Red
  Write-Host "Avez-vous execute 'aws configure' ?" -ForegroundColor Yellow
  exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue

# VPC par defaut
Write-Host ""
Write-Host "VPCs disponibles:" -ForegroundColor Cyan
Write-Host ""

$vpcs = aws ec2 describe-vpcs --region $region --query 'Vpcs[*].[VpcId,IsDefault,CidrBlock]' --output json | ConvertFrom-Json

$defaultVpcId = $null
foreach ($vpc in $vpcs) {
  $vpcId = $vpc[0]
  $isDefault = $vpc[1]
  $cidr = $vpc[2]
    
  if ($isDefault) {
    Write-Host "  VPC ID: $vpcId (Defaut)" -ForegroundColor Green
    $defaultVpcId = $vpcId
  }
  else {
    Write-Host "  VPC ID: $vpcId" -ForegroundColor Gray
  }
  Write-Host "  CIDR: $cidr" -ForegroundColor Gray
}

if (-not $defaultVpcId) {
  $defaultVpcId = $vpcs[0][0]
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue

# Subnets
Write-Host ""
Write-Host "Subnets disponibles dans VPC $defaultVpcId :" -ForegroundColor Cyan
Write-Host ""

$subnets = aws ec2 describe-subnets --region $region --filters "Name=vpc-id,Values=$defaultVpcId" --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock]' --output json | ConvertFrom-Json

$subnetIds = @()
foreach ($subnet in $subnets) {
  $subnetId = $subnet[0]
  $az = $subnet[1]
  $cidr = $subnet[2]
    
  Write-Host "  Subnet ID: $subnetId" -ForegroundColor Yellow
  Write-Host "  Zone: $az" -ForegroundColor Gray
  Write-Host "  CIDR: $cidr" -ForegroundColor Gray
  Write-Host ""
    
  $subnetIds += $subnetId
}

# Prendre les 2 premiers subnets
if ($subnetIds.Count -ge 2) {
  $selectedSubnets = "$($subnetIds[0]),$($subnetIds[1])"
}
else {
  $selectedSubnets = $subnetIds -join ","
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "RESUME - Valeurs a utiliser:" -ForegroundColor Magenta
Write-Host ""
Write-Host "  VpcId:       $defaultVpcId" -ForegroundColor Green
Write-Host "  SubnetIds:   $selectedSubnets" -ForegroundColor Green
Write-Host "  Account ID:  $accountId" -ForegroundColor Green
Write-Host "  Region:      $region" -ForegroundColor Green
Write-Host ""

# Creer le fichier parameters.json
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Creation du fichier parameters.json..." -ForegroundColor Cyan
Write-Host ""

$mistralKey = Read-Host "Entrez votre cle Mistral API"
$jwtSecret = Read-Host "Entrez votre JWT Secret"

$parameters = @"
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "ContainerImage",
    "ParameterValue": "$accountId.dkr.ecr.$region.amazonaws.com/freeda-backend:latest"
  },
  {
    "ParameterKey": "DynamoDBTableName",
    "ParameterValue": "freeda-tickets-production"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "$defaultVpcId"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "$selectedSubnets"
  },
  {
    "ParameterKey": "MistralApiKey",
    "ParameterValue": "$mistralKey"
  },
  {
    "ParameterKey": "JwtSecretKey",
    "ParameterValue": "$jwtSecret"
  }
]
"@

$parametersPath = Join-Path (Get-Location) "parameters.json"
$parameters | Set-Content $parametersPath

Write-Host ""
Write-Host "Fichier parameters.json cree avec succes !" -ForegroundColor Green
Write-Host ""
Write-Host "Emplacement: $parametersPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Vous etes pret pour le deploiement !" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaine etape:" -ForegroundColor Yellow
Write-Host "  cd ..\\.." -ForegroundColor White
Write-Host "  .\\deploy-all.ps1 -Environment production" -ForegroundColor White
Write-Host ""
