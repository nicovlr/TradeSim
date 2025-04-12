from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Configuration de l'application
    APP_NAME: str = "Bourse Traker"
    DEBUG: bool = False
    
    # Configuration de la base de données
    DATABASE_URL: str = "sqlite:///./trading.db"
    
    # Configuration des API
    YAHOO_FINANCE_API: str = "https://query1.finance.yahoo.com/v8/finance/chart/"
    
    # Configuration des stratégies
    DEFAULT_STRATEGIES: List[str] = [
        "SMA Crossover",
        "RSI",
        "Bollinger Bands"
    ]
    
    # Paramètres par défaut
    DEFAULT_PERIOD: str = "1y"
    DEFAULT_WINDOW_SMA: int = 20
    DEFAULT_WINDOW_EMA: int = 20
    DEFAULT_WINDOW_RSI: int = 14
    DEFAULT_WINDOW_BB: int = 20
    DEFAULT_WINDOW_DEV_BB: int = 2
    
    class Config:
        env_file = ".env"

settings = Settings() 