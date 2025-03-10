import sqlite3
import os
import sys

# Ajouter le répertoire racine au PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from utils.logger import logger

def verify_data():
    """Vérifie les données dans la base SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'geogestion.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Récupérer tous les opérateurs
        cursor.execute("""
            SELECT name, contact1, email1, password
            FROM operators
            ORDER BY name;
        """)
        
        operators = cursor.fetchall()
        print("\nListe des opérateurs :")
        print("=" * 80)
        for operator in operators:
            print(f"Nom: {operator[0]}")
            print(f"Contact: {operator[1]}")
            print(f"Email: {operator[2]}")
            print(f"Password: {operator[3]}")
            print("-" * 80)

    except Exception as e:
        print(f"Erreur lors de la vérification des données : {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_data()
