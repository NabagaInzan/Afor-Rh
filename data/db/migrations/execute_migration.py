import sqlite3
import os

def execute_migration():
    try:
        # Chemin vers la base de données
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'geogestion.db')
        
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lecture du fichier SQL
        with open('remove_categorie_from_postes.sql', 'r') as sql_file:
            sql_script = sql_file.read()

        # Exécution du script SQL
        cursor.executescript(sql_script)
        
        # Validation des changements
        conn.commit()
        print("Migration réussie : La colonne 'categorie' a été supprimée de la table 'postes'")

    except Exception as e:
        print(f"Erreur lors de la migration : {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    execute_migration()
