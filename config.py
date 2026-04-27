# ============================================================
#  config.py - Loads all settings from .env
#  MES Wadia COE | LibraMS
# ============================================================

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Flask
    SECRET_KEY  = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key')
    DEBUG       = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Database
    DB_HOST     = os.getenv('DB_HOST', 'localhost')
    DB_USER     = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME     = os.getenv('DB_NAME', 'library_db')

    # App Settings
    FINE_PER_DAY = float(os.getenv('FINE_PER_DAY', 2.00))
    ISSUE_DAYS   = int(os.getenv('ISSUE_DAYS', 14))

    @property
    def DB_CONFIG(self):
        return {
            'host':     self.DB_HOST,
            'user':     self.DB_USER,
            'password': self.DB_PASSWORD,
            'database': self.DB_NAME,
        }

config = Config()