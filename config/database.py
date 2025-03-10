import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from utils.logger import logger

# Charger les variables d'environnement
load_dotenv()

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Vérifier que les variables d'environnement sont chargées
        required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                logger.error(f"Variable d'environnement manquante: {var}")
                raise ValueError(f"La variable d'environnement {var} est requise")
            logger.info(f"Variable {var} trouvée avec la valeur: {value if var != 'DB_PASSWORD' else '*****'}")

        self.connection_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'options': '-c client_encoding=utf8',
            'application_name': os.getenv('APPLICATION_NAME', 'geogestion_app')
        }
        
        logger.info(f"Paramètres de connexion configurés - Host: {self.connection_params['host']}, Port: {self.connection_params['port']}, DB: {self.connection_params['dbname']}")
        self.conn = None

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            if self.conn is None or self.conn.closed:
                logger.info("Tentative de connexion avec les paramètres suivants:")
                safe_params = {k: v if k != 'password' else '*****' for k, v in self.connection_params.items()}
                logger.info(str(safe_params))
                
                self.conn = psycopg2.connect(**self.connection_params)
                self.conn.autocommit = False
                
                # Configuration de l'encodage après la connexion
                with self.conn.cursor() as cursor:
                    cursor.execute("SET client_encoding TO 'UTF8';")
                    cursor.execute("SET standard_conforming_strings TO on;")
                self.conn.commit()
                
                logger.info("Connexion à la base de données établie avec succès")
        except Exception as e:
            logger.error(f"Erreur de connexion à la base de données: {str(e)}")
            raise

    def get_cursor(self):
        """Retourne un curseur avec RealDictCursor pour avoir les résultats sous forme de dictionnaire"""
        if self.conn is None or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def execute_query(self, query, params=None):
        """Exécute une requête et retourne les résultats"""
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params)
            if cursor.description:  # S'il y a des résultats à retourner
                results = cursor.fetchall()
                self.conn.commit()
                return results
            self.conn.commit()
            return None
        except Exception as e:
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()

    def test_connection(self):
        """Teste la connexion à la base de données en exécutant une requête simple"""
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            logger.info(f"Version de PostgreSQL: {result}")
            cursor.close()
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {str(e)}")

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None
            logger.info("Connexion à la base de données fermée")


# Créer une instance unique de la base de données
db = Database()

# Test de la connexion
db.test_connection()
