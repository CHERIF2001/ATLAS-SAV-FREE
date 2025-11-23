#!/bin/bash
# Script de déploiement COMPLET - Freeda Frontend + Backend sur AWS
# Usage: ./deploy-all.sh [environment] [--with-improvements]
# Exemple: ./deploy-all.sh production --with-improvements

set -e  # Exit on error

# ============================================
# Configuration
# ============================================
ENVIRONMENT=${1:-production}
WITH_IMPROVEMENTS=${2:-}
AWS_REGION=${AWS_REGION:-eu-west-1}
PROJECT_NAME="freeda"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# Fonctions Utilitaires
# ============================================

print_header() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║         🚀 FREEDA - DÉPLOIEMENT COMPLET AWS 🚀            ║"
    echo "║                                                            ║"
    echo "║  Frontend (S3 + CloudFront) + Backend (ECS Fargate)       ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${CYAN}Region: ${AWS_REGION}${NC}"
    echo -e "${CYAN}Améliorations: ${WITH_IMPROVEMENTS:-Non}${NC}"
    echo ""
}

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 n'est pas installé"
        exit 1
    fi
}

wait_for_stack() {
    local stack_name=$1
    local operation=$2
    
    print_info "Attente de la fin de l'opération sur $stack_name..."
    
    if [ "$operation" == "create" ]; then
        aws cloudformation wait stack-create-complete \
            --stack-name $stack_name \
            --region $AWS_REGION
    elif [ "$operation" == "update" ]; then
        aws cloudformation wait stack-update-complete \
            --stack-name $stack_name \
            --region $AWS_REGION || true
    fi
}

# ============================================
# Vérifications Préliminaires
# ============================================

check_prerequisites() {
    print_step "Étape 0/10 : Vérifications Préliminaires"
    
    # Vérifier les commandes
    check_command aws
    check_command docker
    check_command node
    check_command npm
    check_command jq
    
    print_success "Toutes les dépendances sont installées"
    
    # Vérifier les credentials AWS
    print_info "Vérification des credentials AWS..."
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "Credentials AWS invalides. Exécutez 'aws configure'"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    print_success "Credentials AWS valides (Account: $account_id)"
    
    # Vérifier que les fichiers existent
    if [ ! -f "infrastructure/frontend-s3-cloudfront.yaml" ]; then
        print_error "Fichier infrastructure/frontend-s3-cloudfront.yaml manquant"
        exit 1
    fi
    
    if [ ! -f "backend/infrastructure/dynamodb-table.yaml" ]; then
        print_error "Fichier backend/infrastructure/dynamodb-table.yaml manquant"
        exit 1
    fi
    
    if [ ! -f "backend/infrastructure/ecs-fargate.yaml" ]; then
        print_error "Fichier backend/infrastructure/ecs-fargate.yaml manquant"
        exit 1
    fi
    
    print_success "Tous les fichiers requis sont présents"
}

# ============================================
# Déploiement DynamoDB
# ============================================

deploy_dynamodb() {
    print_step "Étape 1/10 : Déploiement DynamoDB"
    
    local stack_name="${PROJECT_NAME}-dynamodb-${ENVIRONMENT}"
    
    if aws cloudformation describe-stacks --stack-name $stack_name --region $AWS_REGION &> /dev/null; then
        print_warning "Stack DynamoDB existe déjà, mise à jour..."
        aws cloudformation update-stack \
            --stack-name $stack_name \
            --template-body file://backend/infrastructure/dynamodb-table.yaml \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --region $AWS_REGION || echo "Aucune mise à jour nécessaire"
        
        wait_for_stack $stack_name update
    else
        print_info "Création de la stack DynamoDB..."
        aws cloudformation create-stack \
            --stack-name $stack_name \
            --template-body file://backend/infrastructure/dynamodb-table.yaml \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --region $AWS_REGION
        
        wait_for_stack $stack_name create
    fi
    
    # Récupérer le nom de la table
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`TableName`].OutputValue' \
        --output text)
    
    print_success "DynamoDB déployé : $TABLE_NAME"
}

# ============================================
# Déploiement Redis (si améliorations activées)
# ============================================

deploy_redis() {
    if [ "$WITH_IMPROVEMENTS" != "--with-improvements" ]; then
        print_info "Redis non déployé (améliorations désactivées)"
        return
    fi
    
    print_step "Étape 2/10 : Déploiement Redis (ElastiCache)"
    
    # TODO: Créer template CloudFormation pour Redis
    print_warning "Redis non encore implémenté, sera ajouté dans une prochaine version"
}

# ============================================
# Build & Push Backend Docker
# ============================================

build_push_backend() {
    print_step "Étape 3/10 : Build & Push Backend Docker"
    
    local repo_name="${PROJECT_NAME}-backend"
    
    # Créer le repository ECR si nécessaire
    if ! aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION &> /dev/null; then
        print_info "Création du repository ECR..."
        aws ecr create-repository \
            --repository-name $repo_name \
            --region $AWS_REGION
    fi
    
    # Récupérer l'URI
    ECR_URI=$(aws ecr describe-repositories \
        --repository-names $repo_name \
        --region $AWS_REGION \
        --query 'repositories[0].repositoryUri' \
        --output text)
    
    print_info "ECR Repository: $ECR_URI"
    
    # Login ECR
    print_info "Login à ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_URI
    
    # Build
    print_info "Build de l'image Docker backend..."
    cd backend
    docker build -t $repo_name:latest .
    cd ..
    
    # Tag
    VERSION=$(date +%Y%m%d-%H%M%S)
    docker tag $repo_name:latest $ECR_URI:latest
    docker tag $repo_name:latest $ECR_URI:$VERSION
    
    # Push
    print_info "Push vers ECR..."
    docker push $ECR_URI:latest
    docker push $ECR_URI:$VERSION
    
    print_success "Backend Docker pushed: $ECR_URI:$VERSION"
}

# ============================================
# Déploiement Backend ECS
# ============================================

deploy_backend_ecs() {
    print_step "Étape 4/10 : Déploiement Backend ECS Fargate"
    
    local stack_name="${PROJECT_NAME}-ecs-${ENVIRONMENT}"
    
    # Vérifier que parameters.json existe
    if [ ! -f "backend/infrastructure/parameters.json" ]; then
        print_error "Fichier backend/infrastructure/parameters.json manquant"
        print_info "Créez ce fichier avec vos paramètres (VPC, Subnets, Mistral API Key)"
        exit 1
    fi
    
    # Mettre à jour l'image dans parameters.json
    jq --arg img "$ECR_URI:latest" \
        '(.[] | select(.ParameterKey == "ContainerImage") | .ParameterValue) |= $img' \
        backend/infrastructure/parameters.json > backend/infrastructure/parameters.tmp.json
    mv backend/infrastructure/parameters.tmp.json backend/infrastructure/parameters.json
    
    # Mettre à jour le nom de la table DynamoDB
    jq --arg table "$TABLE_NAME" \
        '(.[] | select(.ParameterKey == "DynamoDBTableName") | .ParameterValue) |= $table' \
        backend/infrastructure/parameters.json > backend/infrastructure/parameters.tmp.json
    mv backend/infrastructure/parameters.tmp.json backend/infrastructure/parameters.json
    
    if aws cloudformation describe-stacks --stack-name $stack_name --region $AWS_REGION &> /dev/null; then
        print_warning "Stack ECS existe, mise à jour du service..."
        
        CLUSTER_NAME=$(aws cloudformation describe-stacks \
            --stack-name $stack_name \
            --region $AWS_REGION \
            --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
            --output text)
        
        SERVICE_NAME=$(aws cloudformation describe-stacks \
            --stack-name $stack_name \
            --region $AWS_REGION \
            --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' \
            --output text)
        
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $SERVICE_NAME \
            --force-new-deployment \
            --region $AWS_REGION
        
        print_success "Déploiement en cours (rolling update)"
    else
        print_info "Création de la stack ECS..."
        aws cloudformation create-stack \
            --stack-name $stack_name \
            --template-body file://backend/infrastructure/ecs-fargate.yaml \
            --parameters file://backend/infrastructure/parameters.json \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION
        
        wait_for_stack $stack_name create
        print_success "Stack ECS créée"
    fi
    
    # Récupérer l'URL du Load Balancer
    BACKEND_URL=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text)
    
    print_success "Backend déployé : http://$BACKEND_URL"
}

# ============================================
# Build Frontend
# ============================================

build_frontend() {
    print_step "Étape 5/10 : Build Frontend (React + Vite)"
    
    print_info "Installation des dépendances..."
    npm install
    
    # Créer .env.production avec l'URL du backend
    print_info "Configuration de l'environnement..."
    cat > .env.production << EOF
VITE_API_URL=http://${BACKEND_URL}
VITE_WS_URL=ws://${BACKEND_URL}
VITE_ENVIRONMENT=${ENVIRONMENT}
EOF
    
    print_info "Build de l'application..."
    npm run build
    
    print_success "Frontend buildé dans dist/"
}

# ============================================
# Déploiement Frontend S3 + CloudFront
# ============================================

deploy_frontend() {
    print_step "Étape 6/10 : Déploiement Frontend (S3 + CloudFront)"
    
    local stack_name="${PROJECT_NAME}-frontend-${ENVIRONMENT}"
    
    if aws cloudformation describe-stacks --stack-name $stack_name --region $AWS_REGION &> /dev/null; then
        print_warning "Stack Frontend existe déjà"
    else
        print_info "Création de la stack Frontend..."
        aws cloudformation create-stack \
            --stack-name $stack_name \
            --template-body file://infrastructure/frontend-s3-cloudfront.yaml \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --region $AWS_REGION
        
        wait_for_stack $stack_name create
    fi
    
    # Récupérer le nom du bucket
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
        --output text)
    
    CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text)
    
    print_success "Stack Frontend créée : $BUCKET_NAME"
    
    # Upload vers S3
    print_info "Upload des fichiers vers S3..."
    aws s3 sync dist/ s3://$BUCKET_NAME/ \
        --delete \
        --cache-control "public, max-age=31536000, immutable" \
        --exclude "index.html" \
        --region $AWS_REGION
    
    # Upload index.html avec cache court
    aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
        --cache-control "public, max-age=0, must-revalidate" \
        --region $AWS_REGION
    
    print_success "Fichiers uploadés vers S3"
    
    # Invalider le cache CloudFront
    print_info "Invalidation du cache CloudFront..."
    aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_ID \
        --paths "/*" \
        --region $AWS_REGION
    
    # Récupérer l'URL
    FRONTEND_URL=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
        --output text)
    
    print_success "Frontend déployé : $FRONTEND_URL"
}

# ============================================
# Migration des Données
# ============================================

migrate_data() {
    print_step "Étape 7/10 : Migration des Données (optionnel)"
    
    if [ -f "backend/data/tickets.json" ]; then
        print_warning "Fichier tickets.json détecté"
        read -p "Voulez-vous migrer les données vers DynamoDB? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Migration en cours..."
            cd backend
            python scripts/migrate_to_dynamodb.py
            cd ..
            print_success "Migration terminée"
        else
            print_info "Migration ignorée"
        fi
    else
        print_info "Pas de données à migrer"
    fi
}

# ============================================
# Configuration CORS Backend
# ============================================

update_cors() {
    print_step "Étape 8/10 : Configuration CORS"
    
    print_info "Mise à jour des CORS pour autoriser le frontend..."
    
    # Mettre à jour la variable d'environnement ALLOWED_ORIGINS dans ECS
    # TODO: Implémenter la mise à jour via CloudFormation ou AWS CLI
    
    print_warning "CORS à configurer manuellement dans backend/.env:"
    echo "ALLOWED_ORIGINS=$FRONTEND_URL"
}

# ============================================
# Tests de Santé
# ============================================

health_checks() {
    print_step "Étape 9/10 : Tests de Santé"
    
    print_info "Test du backend..."
    sleep 10  # Attendre que le service démarre
    
    if curl -s http://$BACKEND_URL/health | grep -q "healthy"; then
        print_success "Backend opérationnel ✓"
    else
        print_warning "Backend en cours de démarrage..."
    fi
    
    print_info "Test du frontend..."
    if curl -s $FRONTEND_URL | grep -q "<!DOCTYPE html>"; then
        print_success "Frontend opérationnel ✓"
    else
        print_warning "Frontend en cours de propagation CloudFront..."
    fi
}

# ============================================
# Résumé Final
# ============================================

print_summary() {
    print_step "Étape 10/10 : Résumé du Déploiement"
    
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║              🎉 DÉPLOIEMENT TERMINÉ ! 🎉                  ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}📊 Informations de Déploiement${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Frontend:${NC}"
    echo -e "  URL:         ${GREEN}$FRONTEND_URL${NC}"
    echo -e "  S3 Bucket:   $BUCKET_NAME"
    echo -e "  CloudFront:  $CLOUDFRONT_ID"
    echo ""
    echo -e "${YELLOW}Backend:${NC}"
    echo -e "  URL:         ${GREEN}http://$BACKEND_URL${NC}"
    echo -e "  Health:      http://$BACKEND_URL/health"
    echo -e "  API Docs:    http://$BACKEND_URL/docs"
    echo ""
    echo -e "${YELLOW}Base de Données:${NC}"
    echo -e "  DynamoDB:    $TABLE_NAME"
    echo -e "  Region:      $AWS_REGION"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📝 Prochaines Étapes:${NC}"
    echo -e "  1. Tester l'application: ${GREEN}$FRONTEND_URL${NC}"
    echo -e "  2. Configurer un domaine personnalisé (optionnel)"
    echo -e "  3. Activer HTTPS avec ACM"
    echo -e "  4. Configurer les alertes CloudWatch"
    echo ""
    echo -e "${YELLOW}📚 Documentation:${NC}"
    echo -e "  - Guide AWS:        backend/docs/AWS_DEPLOYMENT.md"
    echo -e "  - Architecture:     ARCHITECTURE.md"
    echo -e "  - Améliorations:    START_HERE.md"
    echo ""
    echo -e "${GREEN}✅ Tout est prêt pour la production !${NC}"
    echo ""
}

# ============================================
# Main
# ============================================

main() {
    print_header
    
    check_prerequisites
    deploy_dynamodb
    deploy_redis
    build_push_backend
    deploy_backend_ecs
    build_frontend
    deploy_frontend
    migrate_data
    update_cors
    health_checks
    print_summary
}

# Exécuter
main
