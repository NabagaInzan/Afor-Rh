from datetime import datetime
from utils.logger import logger
from config.database import db
import uuid

class SupabaseAuth:
    @staticmethod
    def get_user_by_email(email):
        try:
            logger.info(f"Tentative de récupération de l'utilisateur par email: {email}")
            query = "SELECT * FROM users WHERE email = %s"
            response = db.execute_query(query, (email,))
            user = response[0] if response else None
            logger.info(f"Récupération réussie de l'utilisateur: {email}")
            return user
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
            return None

    @staticmethod
    def get_all_users():
        try:
            logger.info("Tentative de récupération de tous les utilisateurs")
            query = "SELECT * FROM users"
            users = db.execute_query(query)
            logger.info(f"Récupération réussie de {len(users)} utilisateurs")
            return users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
            return []

    @staticmethod
    def verify_password(email, password):
        try:
            logger.info(f"Tentative de vérification du mot de passe pour l'utilisateur: {email}")
            query = "SELECT * FROM users WHERE email = %s AND password = %s"
            response = db.execute_query(query, (email, password))
            if response:
                logger.info(f"Vérification du mot de passe réussie pour l'utilisateur: {email}")
                return response[0]
            logger.error(f"Vérification du mot de passe échouée pour l'utilisateur: {email}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {str(e)}")
            return None

    @staticmethod
    def create_user(email, password, username, role='operateur'):
        try:
            logger.info(f"Tentative de création d'un nouvel utilisateur: {email}")
            query = """
                INSERT INTO users (email, password, username, role, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (email, password, username, role, datetime.utcnow())
            result = db.execute_query(query, params)
            if result:
                logger.info(f"Utilisateur créé avec succès: {email}")
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return None

    @staticmethod
    def log_action(user_id, action, target_table, target_record_id):
        try:
            logger.info(f"Tentative de journalisation de l'action: {action} sur {target_table}")
            query = """
                INSERT INTO action_logs (user_id, action, target_table, target_record_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (user_id, action, target_table, target_record_id, datetime.utcnow())
            db.execute_query(query, params)
            logger.info(f"Journalisation de l'action réussie: {action} sur {target_table}")
        except Exception as e:
            logger.error(f"Erreur lors de la journalisation de l'action: {str(e)}")

class OperatorManager:
    @staticmethod
    def get_all_operators():
        """Récupère tous les opérateurs de la base de données"""
        try:
            query = """
                SELECT id, name, contact1, contact2, email1, email2, address1, address2
                FROM operators
                ORDER BY name;
            """
            results = db.execute_query(query)
            logger.info(f"Récupération réussie de {len(results) if results else 0} opérateurs")
            return results or []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des opérateurs: {str(e)}")
            return []

    @staticmethod
    def get_operator_by_contact(contact):
        """Récupère un opérateur par son contact (contact1 ou contact2)"""
        try:
            query = """
                SELECT id, name, contact1, contact2, email1, email2, address1, address2
                FROM operators
                WHERE contact1 = %s OR contact2 = %s;
            """
            results = db.execute_query(query, (contact, contact))
            if results and len(results) > 0:
                logger.info(f"Opérateur trouvé avec le contact {contact}")
                return results[0]
            logger.warning(f"Aucun opérateur trouvé avec le contact {contact}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de l'opérateur: {str(e)}")
            return None

    @staticmethod
    def create_operator(name, contact1, contact2=None, email1=None, email2=None, address1=None, address2=None):
        """Crée un nouvel opérateur dans la base de données"""
        try:
            query = """
                INSERT INTO operators (id, name, contact1, contact2, email1, email2, address1, address2)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, contact1, contact2, email1, email2, address1, address2;
            """
            operator_id = str(uuid.uuid4())
            results = db.execute_query(query, (
                operator_id, name, contact1, contact2, 
                email1, email2, address1, address2
            ))
            if results and len(results) > 0:
                logger.info(f"Nouvel opérateur créé avec l'ID {operator_id}")
                return results[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'opérateur: {str(e)}")
            return None

    @staticmethod
    def update_operator(operator_id, name=None, contact1=None, contact2=None, email1=None, email2=None, address1=None, address2=None):
        """Met à jour les informations d'un opérateur"""
        try:
            # Construire la requête de mise à jour dynamiquement
            update_fields = []
            params = []
            if name:
                update_fields.append("name = %s")
                params.append(name)
            if contact1:
                update_fields.append("contact1 = %s")
                params.append(contact1)
            if contact2:
                update_fields.append("contact2 = %s")
                params.append(contact2)
            if email1:
                update_fields.append("email1 = %s")
                params.append(email1)
            if email2:
                update_fields.append("email2 = %s")
                params.append(email2)
            if address1:
                update_fields.append("address1 = %s")
                params.append(address1)
            if address2:
                update_fields.append("address2 = %s")
                params.append(address2)

            if not update_fields:
                logger.warning("Aucun champ à mettre à jour")
                return None

            update_fields.append("updated_at = current_timestamp")
            query = f"""
                UPDATE operators 
                SET {", ".join(update_fields)}
                WHERE id = %s
                RETURNING id, name, contact1, contact2, email1, email2, address1, address2;
            """
            params.append(operator_id)
            
            results = db.execute_query(query, tuple(params))
            if results and len(results) > 0:
                logger.info(f"Opérateur {operator_id} mis à jour avec succès")
                return results[0]
            logger.warning(f"Aucun opérateur trouvé avec l'ID {operator_id}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'opérateur: {str(e)}")
            return None

    @staticmethod
    def delete_operator(operator_id):
        """Supprime un opérateur de la base de données"""
        try:
            # Vérifier s'il y a des employés liés à cet opérateur
            check_query = """
                SELECT COUNT(*) as count
                FROM employees
                WHERE operator_id = %s;
            """
            results = db.execute_query(check_query, (operator_id,))
            if results and results[0]['count'] > 0:
                logger.warning(f"Impossible de supprimer l'opérateur {operator_id}: il a des employés associés")
                return False

            query = """
                DELETE FROM operators
                WHERE id = %s
                RETURNING id;
            """
            results = db.execute_query(query, (operator_id,))
            if results and len(results) > 0:
                logger.info(f"Opérateur {operator_id} supprimé avec succès")
                return True
            logger.warning(f"Aucun opérateur trouvé avec l'ID {operator_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'opérateur: {str(e)}")
            return False

    @staticmethod
    def log_action(user_id, action, target_table, target_record_id):
        """Enregistre une action dans les logs"""
        try:
            query = """
                INSERT INTO action_logs (id, user_id, action, target_table, target_record_id)
                VALUES (%s, %s, %s, %s, %s);
            """
            log_id = str(uuid.uuid4())
            db.execute_query(query, (log_id, user_id, action, target_table, target_record_id))
            logger.info(f"Action {action} enregistrée pour l'utilisateur {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'action: {str(e)}")
            return False

class EmployeeManager:
    @staticmethod
    def create_employee(first_name, last_name, position, operator_id, **kwargs):
        try:
            logger.info(f"Tentative de création d'un nouvel employé: {first_name} {last_name}")
            query = """
                INSERT INTO employees (first_name, last_name, position, operator_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """
            params = (first_name, last_name, position, operator_id, datetime.utcnow())
            result = db.execute_query(query, params)
            if result:
                logger.info(f"Employé créé avec succès: {first_name} {last_name}")
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'employé {first_name} {last_name}: {str(e)}")
            return None

    @staticmethod
    def get_employees_by_operator(operator_id):
        try:
            logger.info(f"Recherche des employés pour l'opérateur: {operator_id}")
            query = "SELECT * FROM employees WHERE operator_id = %s"
            employees = db.execute_query(query, (operator_id,))
            logger.info(f"Trouvé {len(employees)} employés pour l'opérateur {operator_id}")
            return employees
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des employés pour l'opérateur {operator_id}: {str(e)}")
            return []
