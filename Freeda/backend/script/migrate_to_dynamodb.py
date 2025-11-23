"""
Script de migration des tickets de JSON vers DynamoDB.
Usage: python migrate_to_dynamodb.py
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage.dynamodb_store import DynamoDBStorage, float_to_decimal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_tickets():
    """Migrer les tickets de JSON vers DynamoDB."""
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Configuration
    json_file = Path(__file__).parent.parent / "data" / "tickets.json"
    table_name = os.getenv("DYNAMODB_TABLE_TICKETS", "freeda-tickets-production")
    region = os.getenv("AWS_REGION", "eu-west-1")
    
    logger.info(f"Starting migration from {json_file} to DynamoDB table '{table_name}'")
    
    # Vérifier que le fichier JSON existe
    if not json_file.exists():
        logger.error(f"JSON file not found: {json_file}")
        return
    
    # Charger les tickets depuis JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            tickets_dict = json.load(f)
        
        tickets = list(tickets_dict.values())
        logger.info(f"Loaded {len(tickets)} tickets from JSON")
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return
    
    # Initialiser DynamoDB
    try:
        storage = DynamoDBStorage(table_name=table_name, region=region)
        logger.info("Connected to DynamoDB")
    except Exception as e:
        logger.error(f"Error connecting to DynamoDB: {e}")
        return
    
    # Migrer chaque ticket
    success_count = 0
    error_count = 0
    
    for i, ticket in enumerate(tickets, 1):
        try:
            await storage.save_ticket(ticket)
            success_count += 1
            logger.info(f"[{i}/{len(tickets)}] Migrated ticket {ticket['ticket_id']}")
        except Exception as e:
            error_count += 1
            logger.error(f"[{i}/{len(tickets)}] Error migrating ticket {ticket.get('ticket_id', 'unknown')}: {e}")
    
    # Résumé
    logger.info("=" * 60)
    logger.info("Migration completed!")
    logger.info(f"Total tickets: {len(tickets)}")
    logger.info(f"Successfully migrated: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("=" * 60)
    
    # Vérification
    if success_count > 0:
        logger.info("Verifying migration...")
        try:
            all_tickets = await storage.list_tickets()
            logger.info(f"✓ Verification successful: {len(all_tickets)} tickets found in DynamoDB")
        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")


async def create_backup():
    """Créer une sauvegarde du fichier JSON avant migration."""
    json_file = Path(__file__).parent.parent / "data" / "tickets.json"
    
    if not json_file.exists():
        logger.warning("No JSON file to backup")
        return
    
    backup_file = json_file.with_suffix('.json.backup')
    
    try:
        import shutil
        shutil.copy2(json_file, backup_file)
        logger.info(f"✓ Backup created: {backup_file}")
    except Exception as e:
        logger.error(f"✗ Failed to create backup: {e}")


async def verify_table_exists(table_name: str, region: str):
    """Vérifier que la table DynamoDB existe."""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        table.load()
        logger.info(f"✓ DynamoDB table '{table_name}' exists")
        return True
    except Exception as e:
        logger.error(f"✗ DynamoDB table '{table_name}' not found: {e}")
        logger.error("Please create the table first using CloudFormation:")
        logger.error("  aws cloudformation create-stack --stack-name freeda-dynamodb \\")
        logger.error("    --template-body file://infrastructure/dynamodb-table.yaml \\")
        logger.error("    --parameters ParameterKey=Environment,ParameterValue=production")
        return False


async def main():
    """Point d'entrée principal."""
    logger.info("=" * 60)
    logger.info("Freeda - Migration JSON to DynamoDB")
    logger.info("=" * 60)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    table_name = os.getenv("DYNAMODB_TABLE_TICKETS", "freeda-tickets-production")
    region = os.getenv("AWS_REGION", "eu-west-1")
    
    # Vérifier que la table existe
    if not await verify_table_exists(table_name, region):
        return
    
    # Demander confirmation
    print("\n⚠️  This will migrate all tickets from JSON to DynamoDB.")
    print(f"   Table: {table_name}")
    print(f"   Region: {region}")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() != 'yes':
        logger.info("Migration cancelled by user")
        return
    
    # Créer une sauvegarde
    await create_backup()
    
    # Lancer la migration
    await migrate_tickets()


if __name__ == "__main__":
    asyncio.run(main())
