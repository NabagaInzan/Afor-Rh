# Scripts de création des tables

Ce dossier contient les scripts nécessaires pour créer et initialiser la base de données Supabase.

## Structure de la base de données

1. **users** - Table des utilisateurs
   - Stocke les informations d'authentification et les rôles

2. **operators** - Table des opérateurs
   - Informations sur les opérateurs (contacts, adresses)

3. **employees** - Table des employés
   - Informations détaillées sur les employés
   - Liée aux opérateurs

4. **action_logs** - Table d'audit
   - Trace toutes les actions effectuées dans l'application

5. **roles** - Table des rôles
   - Définit les différents rôles disponibles

## Utilisation

1. Assurez-vous que les variables d'environnement sont configurées dans le fichier `.env`
   ```
   SUPABASE_URL=votre_url_supabase
   SUPABASE_KEY=votre_clé_supabase
   ```

2. Exécutez le script de création des tables :
   ```bash
   python scripts/create_tables.py
   ```

## Fonctionnalités

- Création automatique de toutes les tables nécessaires
- Mise en place des contraintes et relations
- Création des triggers pour la mise à jour automatique des timestamps
- Insertion des rôles par défaut

## Notes importantes

- Le script vérifie l'existence des tables avant de les créer
- Les erreurs sont gérées et affichées de manière claire
- Les triggers maintiennent automatiquement à jour le champ `updated_at`
