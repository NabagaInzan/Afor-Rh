import sqlite3

def get_db_connection():
    """Établit la connexion à la base de données"""
    conn = sqlite3.connect('data/db/geogestion.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_operator_to_project(operator_name, project_id):
    """Ajoute un opérateur à un projet"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Récupérer l'ID de l'opérateur
        cursor.execute("""
            SELECT id FROM operators 
            WHERE name = ?
        """, (operator_name,))
        operator = cursor.fetchone()

        if not operator:
            print(f"Erreur: Opérateur '{operator_name}' non trouvé")
            return

        # Vérifier si le projet existe
        cursor.execute("""
            SELECT id FROM projects 
            WHERE id = ?
        """, (project_id,))
        project = cursor.fetchone()

        if not project:
            print(f"Erreur: Projet '{project_id}' non trouvé")
            return

        # Ajouter l'association dans operator_projects
        try:
            cursor.execute("""
                INSERT INTO operator_projects (operator_id, project_id)
                VALUES (?, ?)
            """, (operator['id'], project_id))
            
            conn.commit()
            print(f"Association créée : {operator_name} -> {project_id}")
            
        except sqlite3.IntegrityError:
            print(f"Note: L'association existe déjà entre {operator_name} et {project_id}")

    except Exception as e:
        print(f"Une erreur est survenue: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Ajouter CGEDS au projet PASFOR
    add_operator_to_project("CGEDS", "PASFOR")
