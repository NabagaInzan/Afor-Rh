import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Créer le dossier logs s'il n'existe pas
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuration du logger
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Format du log
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler pour fichier
    log_file = os.path.join('logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler pour console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Ajouter les handlers au logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Créer le logger principal
logger = setup_logger('geogestion')
