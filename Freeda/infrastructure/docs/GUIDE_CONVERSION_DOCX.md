# GUIDE : CONVERSION DU TEMPLATE EN .DOCX

## Méthode 1 : Avec Microsoft Word (Recommandé)

1. Ouvrez Microsoft Word
2. Fichier → Ouvrir → Sélectionnez `RAPPORT_TESTS_C3.2_TEMPLATE.md`
3. Word ouvrira le fichier Markdown
4. Fichier → Enregistrer sous → Choisissez format `.docx`
5. Ajustez la mise en forme (titres, tableaux, etc.)

## Méthode 2 : Avec Pandoc (Ligne de commande)

```powershell
# Installer Pandoc (si pas déjà fait)
# https://pandoc.org/installing.html

# Convertir en .docx
pandoc RAPPORT_TESTS_C3.2_TEMPLATE.md -o RAPPORT_TESTS_C3.2.docx

# Avec table des matières
pandoc RAPPORT_TESTS_C3.2_TEMPLATE.md -o RAPPORT_TESTS_C3.2.docx --toc
```

## Méthode 3 : En ligne

1. Allez sur https://cloudconvert.com/md-to-docx
2. Uploadez `RAPPORT_TESTS_C3.2_TEMPLATE.md`
3. Téléchargez le fichier .docx

---

## CHECKLIST AVANT SOUMISSION

### ✅ Contenu
- [ ] Toutes les sections "[À REMPLIR PAR VOUS]" sont complétées
- [ ] Vous avez exécuté les tests et documenté les résultats
- [ ] Vous avez ajouté vos propres analyses (pas de copier-coller d'IA)
- [ ] Les tableaux sont remplis avec vos données
- [ ] Vous avez ajouté des captures d'écran/logs

### ✅ Tests Exécutés
- [ ] Tests unitaires : `pytest backend/tests/ -v`
- [ ] Tests manuels des scénarios (messages courts, longs, emojis, etc.)
- [ ] Tests de performance (mesure des temps de réponse)
- [ ] Tests de charge (10+ tickets simultanés)

### ✅ Documentation
- [ ] Minimum 5 pages de contenu rédigé
- [ ] Tableaux de suivi des bugs remplis
- [ ] Extraits de code avec explications
- [ ] Logs anonymisés (pas de clés API, tokens, etc.)

### ✅ Qualité
- [ ] Orthographe et grammaire vérifiées
- [ ] Structure claire et logique
- [ ] Schémas/diagrammes si pertinent
- [ ] Références au code GitHub

### ✅ Anti-détection IA
- [ ] Texte écrit avec VOS propres mots
- [ ] Phrases naturelles (pas trop parfaites)
- [ ] Votre style d'écriture personnel
- [ ] Exemples concrets de VOTRE projet
- [ ] Erreurs/imperfections acceptables (humaines)

---

## COMMANDES UTILES POUR COLLECTER LES DONNÉES

### Exécuter les tests
```powershell
cd backend
pytest tests/ -v --tb=short > ../test_results.txt
```

### Mesurer le temps de réponse API
```powershell
Measure-Command {
    Invoke-RestMethod -Uri "https://d7itckze71tqe.cloudfront.net/public/tickets/" `
        -Method POST `
        -Body (@{initial_message="Test"} | ConvertTo-Json) `
        -ContentType "application/json"
}
```

### Vérifier la couverture de code
```powershell
cd backend
pytest tests/ --cov=app --cov-report=html
# Ouvrir htmlcov/index.html dans un navigateur
```

### Lister les fonctions non testées
```powershell
cd backend
pytest tests/ --cov=app --cov-report=term-missing
```

---

## CONSEILS POUR RÉDIGER

### ✅ BON EXEMPLE (Personnel)
"Lors de mes tests, j'ai constaté que lorsqu'un utilisateur envoie un message contenant uniquement des emojis (par exemple '😡😡😡'), le système détecte correctement un sentiment négatif grâce à l'analyse de Mistral AI. Cependant, le temps de réponse est plus long (environ 4,2 secondes contre 1,8 secondes pour un message textuel classique). Cela pourrait être dû au fait que..."

### ❌ MAUVAIS EXEMPLE (Généré par IA)
"Le système d'analyse de sentiment utilise des algorithmes avancés de traitement du langage naturel pour identifier avec précision les émotions exprimées dans les messages utilisateurs. Cette approche permet une classification optimale des tickets selon leur urgence et leur tonalité émotionnelle."

---

## STRUCTURE RECOMMANDÉE DU .DOCX FINAL

1. **Page de garde**
   - Titre
   - Votre nom
   - Date
   - Logo école (si applicable)

2. **Sommaire** (généré automatiquement)

3. **Corps du rapport** (5+ pages)
   - Introduction
   - Plan de tests
   - Détection d'anomalies
   - Correctifs
   - Améliorations

4. **Annexes**
   - Logs de tests
   - Captures d'écran
   - Code source (extraits)

---

Bon courage pour votre rapport !
