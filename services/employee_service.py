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
        """Récupère tous les employés d'un opérateur"""
        print(f"Récupération des employés pour l'opérateur: {operator_id}")  # Debug log
        
        if not operator_id:
            print("Erreur: operator_id est vide")
            return []
            
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Vérifier d'abord si l'opérateur existe
            cursor.execute("SELECT id FROM operators WHERE id = ?", (operator_id,))
            if not cursor.fetchone():
                print(f"Erreur: Opérateur {operator_id} non trouvé")
                return []
            
            query = """
                WITH RankedContracts AS (
                    SELECT 
                        c.*,
                        ROW_NUMBER() OVER (PARTITION BY c.employee_id ORDER BY c.start_date DESC) as rn,
                        CASE 
                            WHEN start_date IS NOT NULL AND end_date IS NOT NULL 
                            THEN CAST(ROUND((julianday(end_date) - julianday(start_date)) / 30.44) AS INTEGER)
                            ELSE NULL 
                        END as duration_months
                    FROM contracts c
                    WHERE c.deleted_at IS NULL
                ),
                LastLocations AS (
                    SELECT 
                        el.*,
                        ROW_NUMBER() OVER (PARTITION BY el.employee_id ORDER BY el.date_debut DESC) as rn
                    FROM employee_locations el
                    WHERE el.contract_id IN (SELECT id FROM RankedContracts WHERE rn = 1)
                )
                SELECT 
                    e.id, 
                    e.operator_id,  
                    e.first_name, 
                    e.last_name, 
                    e.gender,
                    e.birth_date,
                    e.contact,
                    e.additional_info,
                    e.availability,
                    c.position as poste_titre,
                    p.id as poste_id,
                    r.nom as region_nom,
                    d.nom as departement_nom,
                    sp.nom as sous_prefecture_nom,
                    c.type as contract_type, 
                    c.start_date, 
                    c.end_date, 
                    CASE 
                        WHEN date('now') > date(c.end_date) THEN 'Expiré'
                        WHEN date('now') >= date(c.start_date) AND date('now') <= date(c.end_date) THEN 'En cours'
                        WHEN date('now') < date(c.start_date) THEN 'À venir'
                    END as contract_status,
                    c.duration_months as contract_duration_months,
                    tp.fonction as categorie_nom
                FROM employees e
                LEFT JOIN RankedContracts c ON e.id = c.employee_id AND c.rn = 1
                LEFT JOIN postes p ON p.id = (
                    SELECT poste_id 
                    FROM contracts 
                    WHERE employee_id = e.id 
                    AND deleted_at IS NULL
                    ORDER BY start_date DESC 
                    LIMIT 1
                )
                LEFT JOIN type_poste tp ON c.categorie = tp.id
                LEFT JOIN LastLocations ll ON e.id = ll.employee_id AND ll.rn = 1
                LEFT JOIN regions r ON ll.region_id = r.id
                LEFT JOIN departements d ON ll.departement_id = d.id
                LEFT JOIN sous_prefectures sp ON ll.sous_prefecture_id = sp.id
                WHERE e.operator_id = ? AND e.deleted_at IS NULL
                ORDER BY e.last_name ASC
            """
            
            cursor.execute(query, (operator_id,))
            employees = []
            
            for row in cursor.fetchall():
                employee = dict(row)
                
                # Log détaillé pour le débogage
                print(f"Employé trouvé:")
                print(f"  ID: {employee['id']}")
                print(f"  Opérateur: {employee['operator_id']}")
                print(f"  Nom: {employee['first_name']} {employee['last_name']}")
                print(f"  Poste: {employee.get('poste_titre')}")
                print(f"  Dates contrat: {employee.get('start_date')} - {employee.get('end_date')}")
                
                # Créer un sous-objet contrat
                contract = {
                    'type': employee.pop('contract_type'),
                    'start_date': employee.pop('start_date'),
                    'end_date': employee.pop('end_date'),
                    'status': employee.pop('contract_status')
                }
                employee['contract'] = contract
                
                # Ajouter le titre du poste
                employee['poste'] = employee.pop('poste_titre', '')
                
                if 'contract_duration_months' in employee:
                    employee['contract_duration_months'] = str(employee['contract_duration_months']) if employee['contract_duration_months'] is not None else ''
                
                employees.append(employee)
            
            print(f"Nombre total d'employés trouvés pour l'opérateur {operator_id}: {len(employees)}")
            return employees
            
        except Exception as e:
            print(f"Erreur dans get_employees_by_operator: {str(e)}")
            return []
            
        finally:
            conn.close()

    def get_employee_by_id(self, employee_id):
        """Récupère un employé par son ID"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, first_name, last_name, position, gender, contact, 
                       birth_date, additional_info
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
                    'additional_info': employee[7]
                }
            return None
        except Exception as e:
            print(f"Erreur dans get_employee_by_id: {str(e)}")
            raise e

    def create_employee(self, data):
        """Crée un nouvel employé"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Formatage des noms
            first_name = self.format_first_name(data.get('first_name', ''))
            last_name = self.format_name(data.get('last_name', ''))
            
            # Générer un ID unique
            employee_id = str(uuid.uuid4())
            
            print("Données reçues:", json.dumps(data, indent=2))  # Debug log
            
            # Déterminer la position
            position = "Non spécifié"
            if data.get('poste_id'):
                cursor.execute("SELECT titre FROM postes WHERE id = ?", (data.get('poste_id'),))
                poste_result = cursor.fetchone()
                if poste_result:
                    position = poste_result[0]

            # Récupérer la catégorie
            categorie = data.get('categorie')
            if categorie:
                cursor.execute("SELECT fonction FROM type_poste WHERE id = ?", (categorie,))
                cat_result = cursor.fetchone()
                if cat_result:
                    categorie_nom = cat_result[0]
            
            query = """
                INSERT INTO employees (
                    id, operator_id, first_name, last_name, 
                    gender, birth_date, contact,
                    contract_duration, additional_info, 
                    region_id, departement_id, sous_prefecture_id,
                    ecole_id, diplome_id, poste_id, position, availability
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                employee_id,
                data.get('operator_id'),
                first_name,
                last_name,
                data.get('gender'),
                data.get('birth_date'),
                data.get('contact'),
                data.get('contract_duration'),
                data.get('additional_info'),
                data.get('region_id'),
                data.get('departement_id'),
                data.get('sous_prefecture_id'),
                data.get('ecole_id'),
                data.get('diplome_id'),
                data.get('poste_id') or None,  
                position,
                'Au siège'
            )
            
            print("Paramètres de la requête:", params)  # Debug log
            cursor.execute(query, params)
            
            # Créer le contrat initial si la durée est spécifiée
            if data.get('contract_duration_months') and data.get('contract_start_date'):
                contract_query = """
                    INSERT INTO contracts (
                        id, employee_id, type, start_date, end_date, status,
                        created_at, updated_at
                    ) VALUES (?, ?, 'CDD', ?, ?, 'En cours', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                start_date = datetime.strptime(data['contract_start_date'], '%Y-%m-%d').date()
                end_date = start_date + timedelta(days=int(data['contract_duration_months']) * 30)
                
                contract_params = (
                    str(uuid.uuid4()),
                    employee_id,
                    start_date.isoformat(),
                    end_date.isoformat()
                )
                
                cursor.execute(contract_query, contract_params)
            
            conn.commit()
            return {'success': True, 'id': employee_id}
            
        except Exception as e:
            print(f"Erreur dans create_employee: {str(e)}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def update_employee(self, employee_id, data):
        """Met à jour les informations d'un employé"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            print("Données reçues pour la mise à jour:", data)  # Debug log
            
            # Formatage des noms
            first_name = self.format_first_name(data.get('first_name', ''))
            last_name = self.format_name(data.get('last_name', ''))
            
            # Mise à jour de l'employé
            query = """
                UPDATE employees 
                SET first_name = ?,
                    last_name = ?,
                    poste_id = ?,
                    gender = ?,
                    birth_date = ?,
                    region_id = ?,
                    departement_id = ?,
                    sous_prefecture_id = ?,
                    additional_info = ?,
                    contact = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            params = (
                first_name,
                last_name,
                data.get('poste_id'),
                data.get('gender'),
                data.get('birth_date'),
                data.get('region_id'),
                data.get('departement_id'),
                data.get('sous_prefecture_id'),
                data.get('additional_info'),
                data.get('contact'),
                employee_id
            )
            
            print("Paramètres de la requête:", params)  # Debug log
            cursor.execute(query, params)
            
            # Mise à jour du contrat si nécessaire
            if data.get('contract_duration_months'):
                contract_query = """
                    INSERT INTO contracts (
                        id, employee_id, type, start_date, end_date, status,
                        created_at, updated_at
                    ) VALUES (?, ?, 'CDD', ?, ?, 'En cours', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=int(data['contract_duration_months']) * 30)
                
                contract_params = (
                    str(uuid.uuid4()),
                    employee_id,
                    start_date.isoformat(),
                    end_date.isoformat()
                )
                
                cursor.execute(contract_query, contract_params)
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur dans update_employee: {str(e)}")
            conn.rollback()
            raise e
        finally:
            conn.close()

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
                    SET poste_id = ?, updated_at = ?
                    WHERE id = ?
                """, (position, datetime.now(), employee_id))
            
            # Récupérer les informations du dernier contrat
            cursor.execute("""
                SELECT salary, poste_id, categorie 
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
                    poste_id, categorie, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                employee_id,
                contract_type,
                start_date.isoformat(),
                end_date.isoformat(),
                position or last_contract['poste_id'],
                'Standard',
                'En cours',
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du renouvellement du contrat : {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_employee_contracts(self, employee_id):
        """Récupère l'historique des contrats d'un employé"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.type,
                    c.start_date,
                    c.end_date,
                    c.salary,
                    c.status,
                    e.poste_id,
                    p.titre as poste_nom,
                    tp.fonction as categorie_nom,
                    CAST((julianday(c.end_date) - julianday(c.start_date)) / 30 AS INTEGER) as duration_months
                FROM contracts c
                JOIN employees e ON c.employee_id = e.id
                LEFT JOIN postes p ON e.poste_id = p.id
                LEFT JOIN type_poste tp ON c.categorie = tp.id
                WHERE c.employee_id = ? AND c.deleted_at IS NULL
                ORDER BY c.start_date DESC
            """
            
            cursor.execute(query, (employee_id,))
            contracts = []
            
            for row in cursor.fetchall():
                contract = dict(row)
                # Formater la durée en mois
                if contract['duration_months']:
                    contract['duration'] = f"{contract['duration_months']} mois"
                else:
                    contract['duration'] = "Non spécifié"
                    
                # Utiliser le nom du poste de l'employé
                contract['poste'] = contract['poste_nom'] or "Non spécifié"
                contract['categorie'] = contract['categorie_nom'] or "Non spécifié"
                    
                contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            print(f"Erreur dans get_employee_contracts: {str(e)}")
            return []
            
        finally:
            conn.close()

    def get_all_employees(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    e.*,
                    r.nom as region_nom,
                    d.nom as departement_nom,
                    sp.nom as sous_prefecture_nom,
                    c.status as contract_status,
                    c.type as contract_type,
                    c.start_date as contract_start_date,
                    c.end_date as contract_end_date,
                    p.titre as poste_titre,
                    CASE 
                        WHEN c.end_date < date('now') THEN 'Expiré'
                        ELSE 'En cours'
                    END as contract_state,
                    CAST(
                        (julianday(c.end_date) - julianday(c.start_date)) / 30 
                        AS INTEGER
                    ) as contract_duration_months
                FROM employees e
                LEFT JOIN regions r ON e.region_id = r.id
                LEFT JOIN departements d ON e.departement_id = d.id
                LEFT JOIN sous_prefectures sp ON e.sous_prefecture_id = sp.id
                LEFT JOIN contracts c ON e.id = c.employee_id
                LEFT JOIN postes p ON e.poste_id = p.id
                WHERE e.deleted_at IS NULL
                AND (c.id IS NULL OR c.id = (
                    SELECT id FROM contracts 
                    WHERE employee_id = e.id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ))
                ORDER BY e.created_at DESC
            """)
            employees = cursor.fetchall()
            return [dict(employee) for employee in employees]
        except Exception as e:
            print(f"Erreur lors de la récupération des employés: {str(e)}")
            return []
        finally:
            conn.close()
