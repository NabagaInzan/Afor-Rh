import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

class AdminService:
    def __init__(self):
        """Initialise le service d'administration"""
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'geogestion.db')
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'backups')
        
        # Créer le dossier de backup s'il n'existe pas
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def get_all_operators(self) -> List[Dict]:
        """Récupère tous les opérateurs avec leurs détails complets"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, contact1, contact2, email1, email2, created_at, updated_at
                FROM operators
                ORDER BY name;
            """)
            
            operators = []
            for row in cursor.fetchall():
                operators.append({
                    'id': row[0],
                    'name': row[1],
                    'contact1': row[2],
                    'contact2': row[3],
                    'email1': row[4],
                    'email2': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            return operators
            
        finally:
            if conn:
                conn.close()

    def create_operator(self, data: Dict) -> Dict:
        """Crée un nouvel opérateur"""
        try:
            # Validation des données requises
            required_fields = ['name', 'password']
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Le champ {field} est requis")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # Générer un ID unique basé sur le timestamp
            operator_id = f"OP{int(datetime.now().timestamp())}"
            
            cursor.execute("""
                INSERT INTO operators (
                    id, name, password, contact1, contact2,
                    email1, email2, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                operator_id,
                data['name'],
                data['password'],
                data.get('contact1', ''),
                data.get('contact2', ''),
                data.get('email1', ''),
                data.get('email2', ''),
                now,
                now
            ))
            
            conn.commit()
            
            # Récupérer l'opérateur créé
            created_operator = self.get_operator_by_id(operator_id)
            if not created_operator:
                raise Exception("Erreur lors de la création de l'opérateur")
                
            return created_operator
            
        except sqlite3.Error as e:
            raise Exception(f"Erreur de base de données: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur lors de la création de l'opérateur: {str(e)}")
        finally:
            if conn:
                conn.close()

    def update_operator(self, operator_id: str, data: Dict) -> Dict:
        """Met à jour un opérateur existant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            # Champs pouvant être mis à jour
            updatable_fields = ['name', 'password', 'contact1', 'contact2', 'email1', 'email2']
            
            for field in updatable_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            # Ajouter la date de mise à jour
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # Ajouter l'ID à la fin des paramètres
            params.append(operator_id)
            
            # Construire et exécuter la requête
            query = f"""
                UPDATE operators 
                SET {', '.join(update_fields)}
                WHERE id = ?;
            """
            
            cursor.execute(query, params)
            conn.commit()
            
            return self.get_operator_by_id(operator_id)
            
        finally:
            if conn:
                conn.close()

    def delete_operator(self, operator_id: str) -> bool:
        """Supprime un opérateur par son ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si l'opérateur existe
            cursor.execute("SELECT id FROM operators WHERE id = ?", (operator_id,))
            if not cursor.fetchone():
                return False
                
            # Supprimer l'opérateur
            cursor.execute("DELETE FROM operators WHERE id = ?", (operator_id,))
            conn.commit()
            
            return True
            
        except sqlite3.Error as e:
            raise Exception(f"Erreur de base de données: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_operator_by_id(self, operator_id: str) -> Optional[Dict]:
        """Récupère un opérateur par son ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, contact1, contact2, email1, email2, created_at, updated_at
                FROM operators
                WHERE id = ?;
            """, (operator_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'contact1': row[2],
                    'contact2': row[3],
                    'email1': row[4],
                    'email2': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            
            return None
            
        finally:
            if conn:
                conn.close()

    def get_database_backup(self) -> str:
        """Crée une copie de la base de données et retourne le chemin du fichier"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'geogestion_backup_{timestamp}.db')
        
        # Copier la base de données
        shutil.copy2(self.db_path, backup_path)
        
        return backup_path
