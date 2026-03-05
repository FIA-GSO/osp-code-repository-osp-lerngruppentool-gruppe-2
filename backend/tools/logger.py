from loguru import logger
import os

# --- CONFIGURATION ---
# Erstellt automatisch einen Ordner "logs" und eine Datei darin.
# 'rotation' begrenzt die Dateigröße auf 500 MB, danach wird eine neue Log-Datei erstellt.
logger.add("logs/app.log", rotation="500 MB", level="INFO")

def log(msg, level="info"):
    """Einfache Wrapper-Methode nach deinem Wunsch"""
    if level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)