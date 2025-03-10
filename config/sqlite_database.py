import sqlite3
import os
from utils.logger import logger

class SQLiteDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLiteDatabase, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise la connexion à la base de données SQLite"""
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite')
        self.conn = None

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
                # Configurer la connexion pour retourner les résultats comme des dictionnaires
                self.conn.row_factory = sqlite3.Row
                # Activer les clés étrangères
                self.conn.execute("PRAGMA foreign_keys = ON")
                logger.info("Connexion à la base de données SQLite établie avec succès")
        except Exception as e:
            logger.error(f"Erreur de connexion à la base de données: {str(e)}")
            raise

    def get_cursor(self):
        """Retourne un curseur pour la base de données"""
        if self.conn is None:
            self.connect()
        return self.conn.cursor()

    def execute_query(self, query, params=None):
        """Exécute une requête et retourne les résultats"""
        cursor = None
        try:
            cursor = self.get_cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if cursor.description:  # S'il y a des résultats à retourner
                # Convertir les résultats en dictionnaires
                columns = [col[0] for col in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                self.conn.commit()
                return results
            
            self.conn.commit()
            return None

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()

    def test_connection(self):
        """Teste la connexion à la base de données"""
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            logger.info(f"Version de SQLite: {version}")
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion: {str(e)}")
            return False

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Connexion à la base de données fermée")

# Créer une instance unique de la base de données
db = SQLiteDatabase()
