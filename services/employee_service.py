import sqlite3
import uuid
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class EmployeeService:
    def __init__(self):
        self.db_path = "data/db/geogestion.db"

    def format_name(self, name):
        """Format le nom en majuscules"""
        return name.upper() if name else ""

    def format_first_name(self, name):
        """Format le prénom avec première lettre en majuscule"""
        return name.capitalize() if name else ""

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def calculate_age(self, birth_date_str):
        """Calcule l'âge exact à partir de la date de naissance"""
        if not birth_date_str:
            return None
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth_date.year
            # Vérifier si l'anniversaire n'est pas encore passé cette année
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except:
            return None

    def get_employees_by_operator(self, operator_id):
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            query = """
                WITH RankedContracts AS (
                    SELECT 
                        c.*,
                        ROW_NUMBER() OVER (PARTITION BY c.employee_id ORDER BY c.start_date DESC) as rn
                    FROM contracts c
                )
                SELECT 
                    e.id, e.first_name, e.last_name, e.position, e.contact, e.gender,
                    CASE 
                        WHEN e.availability = 'Disponible' THEN 'Au siège'
                        ELSE 'À l''intérieur'
                    END as availability,
                    e.created_at, e.updated_at, e.birth_date,
                    c.type as contract_type, c.start_date, c.end_date, c.salary,
                    c.department, 
                    CASE 
                        WHEN c.status = 'En cours' THEN 'En cours'
                        ELSE 'Expiré'
                    END as contract_status,
                    e.contract_duration,
                    e.additional_info
                FROM employees e
                LEFT JOIN RankedContracts c ON e.id = c.employee_id AND c.rn = 1
                WHERE e.operator_id = ?
                ORDER BY e.last_name ASC
            """
            cursor.execute(query, (operator_id,))
            employees = []
            for row in cursor.fetchall():
                employee = dict(row)
                
                # Calculer l'âge à partir de la date de naissance
                birth_date = employee.get('birth_date')
                age = None
                if birth_date:
                    try:
                        print(f"Date de naissance trouvée: {birth_date}")  # Debug log
                        birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
                        today = datetime.now()
                        age = today.year - birth_date.year
                        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                            age -= 1
                        print(f"Âge calculé: {age}")  # Debug log
                    except Exception as e:
                        print(f"Erreur lors du calcul de l'âge: {str(e)}")  # Debug log
                        age = None
                
                employee['age'] = age
                
                # Créer un sous-objet contrat
                contract = {
                    'type': employee.pop('contract_type'),
                    'start_date': employee.pop('start_date'),
                    'end_date': employee.pop('end_date'),
                    'salary': employee.pop('salary'),
                    'department': employee.pop('department'),
                    'status': employee.pop('contract_status'),
                    'duration': employee.pop('contract_duration')
                }
                employee['contract'] = contract
                employees.append(employee)
            return employees
        finally:
            conn.close()

    def get_employee_by_id(self, employee_id):
        """Récupère un employé par son ID"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, first_name, last_name, position, gender, contact, 
                       birth_date, contract_duration, additional_info
                FROM employees 
                WHERE id = ?
            """, (employee_id,))
            employee = cursor.fetchone()
            conn.close()
            
            if employee:
                return {
                    'id': employee[0],
                    'first_name': employee[1],
                    'last_name': employee[2],
                    'position': employee[3],
                    'gender': employee[4],
                    'contact': employee[5],
                    'birth_date': employee[6],
                    'contract_duration': employee[7],
                    'additional_info': employee[8]
                }
            return None
        except Exception as e:
            print(f"Erreur dans get_employee_by_id: {str(e)}")
            raise e

    def add_employee(self, data):
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            employee_id = str(uuid.uuid4())
            
            # Debug logs
            print("Début de add_employee avec les données:", json.dumps(data, indent=2))
            
            # Formatage des noms
            first_name = self.format_first_name(data.get('first_name', ''))
            last_name = self.format_name(data.get('last_name', ''))
            
            # Gestion de la date de début du contrat
            contract_start_date = data.get('contract_start_date')
            if not contract_start_date:
                contract_start_date = datetime.now().date().isoformat()
            
            # Formatage de la durée du contrat
            contract_duration = data.get('contract_duration')
            if contract_duration:
                try:
                    contract_duration = str(int(contract_duration))
                except (ValueError, TypeError):
                    contract_duration = '3'
            else:
                contract_duration = '3'
            
            # Insérer l'employé (sans les données de localisation)
            query = """
                INSERT INTO employees (
                    id, first_name, last_name, position, contact, gender,
                    contract_duration, birth_date, operator_id, 
                    additional_info, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                employee_id,
                first_name,
                last_name,
                data.get('position'),
                data.get('contact'),
                data.get('gender'),
                contract_duration,
                data.get('birth_date'),
                data.get('operator_id'),
                data.get('additional_info'),
                now,
                now
            ))
            
            # Créer le contrat initial
            try:
                start_date = datetime.fromisoformat(contract_start_date).date()
                duration_months = int(contract_duration)
                end_date = start_date + timedelta(days=duration_months * 30)
                
                contract_id = str(uuid.uuid4())
                contract_query = """
                    INSERT INTO contracts (
                        id, employee_id, type, start_date, end_date,
                        position, category, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(contract_query, (
                    contract_id,
                    employee_id,
                    'CDD',
                    start_date.isoformat(),
                    end_date.isoformat(),
                    data.get('position'),
                    'Standard',
                    now,
                    now
                ))

                # Ajouter l'entrée de localisation si nécessaire
                if data.get('location') == 'interieur' and all([data.get('region'), data.get('departement'), data.get('sousprefecture')]):
                    location_query = """
                        INSERT INTO employee_locations (
                            id, employee_id, contract_id, region_id, 
                            departement_id, sous_prefecture_id,
                            date_debut, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(location_query, (
                        str(uuid.uuid4()),
                        employee_id,
                        contract_id,
                        data.get('region'),
                        data.get('departement'),
                        data.get('sousprefecture'),
                        start_date.isoformat(),
                        now,
                        now
                    ))
                
                conn.commit()
                return True
                
            except Exception as e:
                print(f"Erreur lors de la création du contrat: {str(e)}")
                conn.rollback()
                return False
                
        except Exception as e:
            print(f"Erreur lors de l'ajout d'un employé: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_employee(self, employee_id, data):
        """Met à jour un employé"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Vérifier si l'employé existe
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            # Mettre à jour l'employé
            cursor.execute("""
                UPDATE employees 
                SET first_name = ?,
                    last_name = ?,
                    position = ?,
                    gender = ?,
                    contact = ?,
                    birth_date = ?,
                    contract_duration = ?,
                    additional_info = ?
                WHERE id = ?
            """, (
                data.get('first_name'),
                data.get('last_name'),
                data.get('position'),
                data.get('gender'),
                data.get('contact'),
                data.get('birth_date'),
                data.get('contract_duration'),
                data.get('additional_info'),
                employee_id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur dans update_employee: {str(e)}")
            raise e

    def delete_employee(self, employee_id):
        """Supprime un employé"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Vérifier si l'employé existe
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            # Supprimer l'employé
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erreur dans delete_employee: {str(e)}")
            raise e

    def get_employee_stats(self, operator_id):
        """Récupère les statistiques des employés"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Total des employés
            cursor.execute("""
                SELECT COUNT(*) 
                FROM employees 
                WHERE operator_id = ?
            """, (operator_id,))
            total = cursor.fetchone()[0] or 0
            
            # Employés par disponibilité
            cursor.execute("""
                SELECT region_id, COUNT(*) 
                FROM employees 
                WHERE operator_id = ? 
                GROUP BY region_id
            """, (operator_id,))
            region_counts = dict(cursor.fetchall())
            
            # Employés par genre
            cursor.execute("""
                SELECT gender, COUNT(*) 
                FROM employees 
                WHERE operator_id = ? 
                GROUP BY gender
            """, (operator_id,))
            gender_results = cursor.fetchall()
            male = 0
            female = 0
            for gender, count in gender_results:
                if gender in ['M', 'Homme', 'H']:
                    male += count
                elif gender in ['F', 'Femme']:
                    female += count
            
            return {
                'success': True,
                'stats': {
                    'total': total,
                    'regions': region_counts,
                    'male': male,
                    'female': female
                }
            }
        except Exception as e:
            print(f"Erreur dans get_employee_stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if conn:
                conn.close()

    def renew_contract(self, employee_id, contract_type, duration, position=None):
        """Renouvelle le contrat d'un employé"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Vérifier si l'employé existe
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                return False
            
            # Marquer l'ancien contrat comme expiré
            cursor.execute("""
                UPDATE contracts 
                SET status = 'Expiré', updated_at = ?
                WHERE employee_id = ? AND status = 'En cours'
            """, (datetime.now(), employee_id))
            
            # Créer le nouveau contrat
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=int(duration) * 30)  # Approximation mois
            
            # Si un nouveau poste est spécifié, l'utiliser
            if position:
                cursor.execute("""
                    UPDATE employees 
                    SET position = ?, updated_at = ?
                    WHERE id = ?
                """, (position, datetime.now(), employee_id))
            
            # Récupérer les informations du dernier contrat
            cursor.execute("""
                SELECT salary, department, position 
                FROM contracts 
                WHERE employee_id = ? 
                ORDER BY end_date DESC 
                LIMIT 1
            """, (employee_id,))
            last_contract = cursor.fetchone()
            
            if not last_contract:
                return False
                
            cursor.execute("""
                INSERT INTO contracts (
                    id, employee_id, type, start_date, end_date,
                    position, category, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                employee_id,
                contract_type,
                start_date,
                end_date,
                position or last_contract['position'],
                'Standard',
                datetime.now(),
                datetime.now()
            ))
            
            # Mettre à jour la durée du contrat dans la table employees
            cursor.execute("""
                UPDATE employees 
                SET contract_duration = ?, updated_at = ?
                WHERE id = ?
            """, (
                f"{duration} mois",
                datetime.now(),
                employee_id
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du renouvellement du contrat : {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
