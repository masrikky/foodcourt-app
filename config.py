# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-rahasia-super-sulit-ditebak-jangan-pakai-ini-di-produksi-asli-sialan'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///foodcourt.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False