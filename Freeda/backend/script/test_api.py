#!/usr/bin/env python3
"""
Script de test pour vérifier que l'API Freeda fonctionne correctement.
"""

import httpx
import asyncio
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def test_api():
    """Teste les endpoints principaux de l'API."""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Tests de l'API Freeda\n")
        
        # 1. Health check
        print("1️⃣ Test du health check...")
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check OK: {data}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            print("   ℹ️  Assurez-vous que le backend est démarré (uvicorn main:app --reload)")
            return
        
        # 2. Créer un ticket
        print("\n2️⃣ Test de création de ticket...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/tickets",
                json={"initial_message": "Test: Problème de connexion internet"}
            )
            if response.status_code == 200:
                ticket = response.json()
                ticket_id = ticket["ticket_id"]
                print(f"   ✅ Ticket créé: {ticket_id}")
                print(f"   📊 Analytics: {ticket.get('analytics', 'Non disponible')}")
            else:
                print(f"   ❌ Création échouée: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return
        
        # 3. Lister les tickets
        print("\n3️⃣ Test de listing des tickets...")
        try:
            response = await client.get(f"{API_BASE_URL}/tickets")
            if response.status_code == 200:
                tickets = response.json()
                print(f"   ✅ {len(tickets)} ticket(s) trouvé(s)")
            else:
                print(f"   ❌ Listing échoué: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 4. Récupérer le ticket
        print("\n4️⃣ Test de récupération du ticket...")
        try:
            response = await client.get(f"{API_BASE_URL}/tickets/{ticket_id}")
            if response.status_code == 200:
                ticket = response.json()
                print(f"   ✅ Ticket récupéré")
                print(f"   📝 Messages: {len(ticket['messages'])}")
                print(f"   📊 Statut: {ticket['status']}")
            else:
                print(f"   ❌ Récupération échouée: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 5. Envoyer un message
        print("\n5️⃣ Test d'envoi de message...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/tickets/{ticket_id}/messages",
                json={"message": "Le problème persiste depuis ce matin"}
            )
            if response.status_code == 200:
                message = response.json()
                print(f"   ✅ Message envoyé")
                print(f"   💬 Réponse: {message['content'][:100]}...")
            else:
                print(f"   ❌ Envoi échoué: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 6. Fermer le ticket
        print("\n6️⃣ Test de fermeture du ticket...")
        try:
            response = await client.patch(
                f"{API_BASE_URL}/tickets/{ticket_id}/status",
                json={"status": "fermé"}
            )
            if response.status_code == 200:
                ticket = response.json()
                print(f"   ✅ Ticket fermé")
                print(f"   ⏱️  Durée de résolution: {ticket.get('resolution_duration', 'N/A')} secondes")
            else:
                print(f"   ❌ Fermeture échouée: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # 7. Export CSV
        print("\n7️⃣ Test d'export CSV...")
        try:
            response = await client.get(f"{API_BASE_URL}/export/csv")
            if response.status_code == 200:
                csv_content = response.text
                lines = csv_content.split('\n')
                print(f"   ✅ CSV généré: {len(lines)} lignes")
                print(f"   📄 Header: {lines[0][:100]}...")
            else:
                print(f"   ❌ Export échoué: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print("\n✅ Tests terminés!\n")

if __name__ == "__main__":
    asyncio.run(test_api())
