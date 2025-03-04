import sqlite3
import os

def export_schema(db_path, output_file):
    if not os.path.exists(db_path):
        print(f"Erreur: La base de données {db_path} n'existe pas.")
        return
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Récupération du schéma de la base de données
        cursor.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'index', 'trigger', 'view') AND sql IS NOT NULL;")
        schema = cursor.fetchall()
        
        if not schema:
            print("Aucune structure trouvée dans la base de données.")
            return
        
        # Création du répertoire de sortie s'il n'existe pas
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Écriture dans le fichier
        with open(output_file, "w", encoding="utf-8") as file:
            for entry in schema:
                file.write(entry[0] + "\n\n")
        
        print(f"Schéma exporté avec succès dans {output_file}")
    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# Chemin de la base de données et fichier de sortie
export_schema("data/db/geogestion.db", "data/db/schema.txt")
