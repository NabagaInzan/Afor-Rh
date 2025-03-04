import sqlite3
from datetime import datetime

def get_db_connection():
    """Établit la connexion à la base de données"""
    conn = sqlite3.connect('data/db/geogestion.db')
    conn.row_factory = sqlite3.Row
    return conn

def fill_school_projects():
    """Remplit la table school_projects en associant chaque école à tous les projets"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Récupérer tous les projets
        cursor.execute("SELECT id FROM projects")
        projects = cursor.fetchall()

        # Récupérer toutes les écoles
        cursor.execute("SELECT id FROM ecoles")
        schools = cursor.fetchall()
        
        # Convertir les résultats en listes
        project_ids = [project['id'] for project in projects]
        school_ids = [school['id'] for school in schools]

        if not project_ids or not school_ids:
            print("Erreur: Aucun projet ou aucune école trouvé")
            return

        # Vider la table school_projects avant de la remplir
        cursor.execute("DELETE FROM school_projects")
        
        # Pour chaque école, l'associer à tous les projets
        for school_id in school_ids:
            for project_id in project_ids:
                try:
                    # Insérer l'association dans school_projects
                    cursor.execute("""
                        INSERT INTO school_projects (school_id, project_id)
                        VALUES (?, ?)
                    """, (school_id, project_id))
                    
                    print(f"Association créée : École {school_id} -> Projet {project_id}")
                    
                except sqlite3.IntegrityError as e:
                    print(f"Erreur d'intégrité pour École {school_id} -> Projet {project_id}: {e}")
                    continue

        # Valider les changements
        conn.commit()
        print("\nRemplissage de school_projects terminé avec succès!")

    except Exception as e:
        print(f"Une erreur est survenue: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fill_school_projects()
