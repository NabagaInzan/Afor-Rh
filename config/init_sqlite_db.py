import sqlite3
import os
import sys
from datetime import datetime
import uuid

# Ajouter le répertoire racine au PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from utils.logger import logger

def init_database():
    """Initialise la base de données SQLite avec la structure requise"""
    # Créer le chemin de la base de données
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    db_path = os.path.join(db_dir, 'geogestion.db')
    
    # Supprimer la base de données existante si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Base de données existante supprimée")
    
    try:
        # Créer une connexion à la base de données (la crée si elle n'existe pas)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Activer les clés étrangères
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Créer les tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            contact1 TEXT,
            contact2 TEXT,
            address1 TEXT,
            address2 TEXT,
            email1 TEXT,
            email2 TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            position TEXT NOT NULL,
            contact TEXT,
            gender TEXT,
            contract_duration TEXT,
            birth_date DATE,
            operator_id TEXT,
            availability TEXT,
            salary DECIMAL(10, 2),
            additional_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operator_id) REFERENCES operators(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            action TEXT NOT NULL,
            target_table TEXT NOT NULL,
            target_record_id TEXT,
            action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id TEXT PRIMARY KEY,
            role_name TEXT NOT NULL,
            description TEXT
        );
        """)

        # Créer les triggers pour la mise à jour automatique de updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_user_timestamp 
        AFTER UPDATE ON users
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_operator_timestamp 
        AFTER UPDATE ON operators
        BEGIN
            UPDATE operators SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_employee_timestamp 
        AFTER UPDATE ON employees
        BEGIN
            UPDATE employees SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """)

        # Insérer les rôles par défaut s'ils n'existent pas déjà
        cursor.execute("SELECT COUNT(*) FROM roles WHERE role_name = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO roles (id, role_name, description)
            VALUES (?, 'admin', 'Administrateur de l''application');
            """, (str(uuid.uuid4()),))

        cursor.execute("SELECT COUNT(*) FROM roles WHERE role_name = 'operateur'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO roles (id, role_name, description)
            VALUES (?, 'operateur', 'Opérateur responsable de la gestion des employés');
            """, (str(uuid.uuid4()),))

        # Valider les changements
        conn.commit()
        logger.info("Base de données SQLite initialisée avec succès")
        
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database()
