import sqlite3
import os
from typing import List, Dict, Optional

class SQLiteAuth:
    def __init__(self):
        """Initialise la connexion à la base de données SQLite"""
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'geogestion.db')
        self._init_db()

    def _init_db(self):
        """Initialise la base de données avec les tables nécessaires"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Créer la table des administrateurs si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS administrators (
                    phone TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            
            # Vérifier si l'administrateur par défaut existe
            cursor.execute("SELECT COUNT(*) FROM administrators WHERE phone = ?", ("0576610155",))
            if cursor.fetchone()[0] == 0:
                # Ajouter l'administrateur par défaut
                from datetime import datetime
                now = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO administrators (phone, name, password, email, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, ("0576610155", "Admin Principal", "Admin123", "admin@geogestion.com", now, now))
            
            # Créer la table des opérateurs si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operators (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact1 TEXT NOT NULL,
                    email1 TEXT,
                    password TEXT NOT NULL
                );
            """)
            
            conn.commit()
            
        finally:
            if conn:
                conn.close()

    def get_operators(self) -> List[Dict]:
        """Récupère la liste de tous les opérateurs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, contact1, email1
                FROM operators
                ORDER BY name;
            """)
            
            operators = []
            for row in cursor.fetchall():
                operators.append({
                    'id': row[0],
                    'name': row[1],
                    'contact': row[2],
                    'email': row[3]
                })
            
            return operators
            
        except Exception as e:
            print(f"Erreur lors de la récupération des opérateurs : {str(e)}")
            return []
            
        finally:
            if conn:
                conn.close()

    def verify_operator_password(self, operator_id: str, password: str) -> bool:
        """Vérifie le mot de passe d'un opérateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT password
                FROM operators
                WHERE id = ?;
            """, (operator_id,))
            
            result = cursor.fetchone()
            if result:
                return result[0] == password
            return False
            
        except Exception as e:
            print(f"Erreur lors de la vérification du mot de passe : {str(e)}")
            return False
            
        finally:
            if conn:
                conn.close()

    def get_operator_by_id(self, operator_id: str) -> Optional[Dict]:
        """Récupère les informations d'un opérateur par son ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, contact1, email1
                FROM operators
                WHERE id = ?;
            """, (operator_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'contact': row[2],
                    'email': row[3]
                }
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'opérateur : {str(e)}")
            return None
            
        finally:
            if conn:
                conn.close()

    def verify_admin_credentials(self, phone: str, password: str) -> bool:
        """Vérifie les identifiants de l'administrateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT password
                FROM administrators
                WHERE phone = ?;
            """, (phone,))
            
            result = cursor.fetchone()
            if result:
                return result[0] == password
            return False
            
        finally:
            if conn:
                conn.close()

    def get_admin_by_phone(self, phone: str) -> Optional[Dict]:
        """Récupère les informations d'un administrateur par son numéro de téléphone"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT phone, name, email, created_at, updated_at
                FROM administrators
                WHERE phone = ?;
            """, (phone,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'phone': row[0],
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3],
                    'updated_at': row[4]
                }
            return None
            
        finally:
            if conn:
                conn.close()

    def get_all_admins(self) -> List[Dict]:
        """Récupère la liste de tous les administrateurs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT phone, name, email, created_at, updated_at
                FROM administrators
                ORDER BY name;
            """)
            
            admins = []
            for row in cursor.fetchall():
                admins.append({
                    'phone': row[0],
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3],
                    'updated_at': row[4]
                })
            
            return admins
            
        finally:
            if conn:
                conn.close()

    def create_admin(self, data: Dict) -> Dict:
        """Crée un nouvel administrateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            from datetime import datetime
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO administrators (
                    phone, name, password, email, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?);
            """, (
                data['phone'],
                data['name'],
                data['password'],
                data.get('email'),
                now,
                now
            ))
            
            conn.commit()
            
            return self.get_admin_by_phone(data['phone'])
            
        finally:
            if conn:
                conn.close()

    def update_admin(self, phone: str, data: Dict) -> Dict:
        """Met à jour un administrateur existant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            for field in ['name', 'password', 'email']:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            from datetime import datetime
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(phone)
            
            cursor.execute(f"""
                UPDATE administrators
                SET {', '.join(update_fields)}
                WHERE phone = ?;
            """, params)
            
            conn.commit()
            
            return self.get_admin_by_phone(phone)
            
        finally:
            if conn:
                conn.close()

    def delete_admin(self, phone: str) -> None:
        """Supprime un administrateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM administrators WHERE phone = ?;", (phone,))
            conn.commit()
            
        finally:
            if conn:
                conn.close()
