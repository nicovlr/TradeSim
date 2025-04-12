import pandas as pd
import numpy as np
import yfinance as yf
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from datetime import datetime, timedelta

class TradingService:
    def __init__(self, symbol="MC.PA", period="1y"):  # MC.PA est le symbole de LVMH sur Yahoo Finance
        self.symbol = symbol
        self.period = period
        print(f"Initialisation du service avec le symbole {self.symbol} et la période {self.period}")
        self.data = self._load_data()
        
    def _load_data(self):
        """Charge les données historiques"""
        try:
            print(f"Tentative de chargement des données pour {self.symbol}")
            
            # Création d'un objet Ticker
            ticker = yf.Ticker(self.symbol)
            
            # Récupération des informations sur le ticker
            info = ticker.info
            print(f"Informations sur le ticker : {info.get('longName', 'Non disponible')}")
            
            # Détermination de l'intervalle en fonction de la période
            interval = '1m' if self.period == '1d' else '1d'
            
            # Téléchargement des données avec plus d'options
            data = ticker.history(
                period=self.period,
                interval=interval,
                auto_adjust=True,
                prepost=True
            )
            
            print(f"Données téléchargées : {len(data)} lignes")
            print(f"Colonnes disponibles : {data.columns.tolist()}")
            
            if data.empty:
                print(f"Aucune donnée disponible pour {self.symbol}")
                return None
                
            # Vérification que nous avons des données valides
            if len(data) < 2:
                print(f"Pas assez de données pour {self.symbol}")
                return None
                
            print(f"Données chargées avec succès pour {self.symbol}")
            print(f"Première date : {data.index[0]}")
            print(f"Dernière date : {data.index[-1]}")
            return data
        except Exception as e:
            print(f"Erreur lors du chargement des données pour {self.symbol}: {str(e)}")
            return None

    def calculate_sma(self, window=20):
        """Calcule la moyenne mobile simple"""
        if self.data is not None and not self.data.empty:
            sma = SMAIndicator(close=self.data['Close'], window=window)
            return sma.sma_indicator()
        return None

    def calculate_ema(self, window=20):
        """Calcule la moyenne mobile exponentielle"""
        if self.data is not None and not self.data.empty:
            ema = EMAIndicator(close=self.data['Close'], window=window)
            return ema.ema_indicator()
        return None

    def calculate_rsi(self, window=14):
        """Calcule l'indicateur RSI"""
        if self.data is not None and not self.data.empty:
            rsi = RSIIndicator(close=self.data['Close'], window=window)
            return rsi.rsi()
        return None

    def calculate_bollinger_bands(self, window=20, window_dev=2):
        """Calcule les bandes de Bollinger"""
        if self.data is not None and not self.data.empty:
            bb = BollingerBands(close=self.data['Close'], window=window, window_dev=window_dev)
            return {
                'upper': bb.bollinger_hband(),
                'middle': bb.bollinger_mavg(),
                'lower': bb.bollinger_lband()
            }
        return None

    def sma_crossover_strategy(self, short_window=20, long_window=50):
        """Implémente une stratégie de croisement des moyennes mobiles"""
        if self.data is not None and not self.data.empty:
            # Calcul des moyennes mobiles
            short_sma = self.calculate_sma(window=short_window)
            long_sma = self.calculate_sma(window=long_window)
            
            if short_sma is None or long_sma is None:
                return None
                
            # Création des signaux
            signals = pd.DataFrame(index=self.data.index)
            signals['signal'] = 0.0
            
            # Signal d'achat (1) quand la SMA courte croise la SMA longue par le haut
            signals.loc[short_sma > long_sma, 'signal'] = 1.0
            
            # Génération des signaux de trading
            signals['positions'] = signals['signal'].diff()
            
            return signals
        return None

    def rsi_strategy(self, window=14, overbought=70, oversold=30):
        """Implémente une stratégie basée sur le RSI"""
        if self.data is not None and not self.data.empty:
            rsi = self.calculate_rsi(window=window)
            
            if rsi is None:
                return None
                
            signals = pd.DataFrame(index=self.data.index)
            signals['signal'] = 0.0
            
            # Signal d'achat quand RSI < oversold
            signals.loc[rsi < oversold, 'signal'] = 1.0
            # Signal de vente quand RSI > overbought
            signals.loc[rsi > overbought, 'signal'] = -1.0
            
            signals['positions'] = signals['signal'].diff()
            
            return signals
        return None

    def backtest_strategy(self, strategy_func, initial_capital=10000.0):
        """Effectue un backtest avec la stratégie fournie"""
        if self.data is not None and not self.data.empty:
            signals = strategy_func()
            if signals is not None and not signals.empty:
                portfolio = pd.DataFrame(index=self.data.index)
                portfolio['holdings'] = signals['signal'] * self.data['Close']
                portfolio['cash'] = initial_capital - (signals['signal'].diff() * self.data['Close']).cumsum()
                portfolio['total'] = portfolio['holdings'] + portfolio['cash']
                
                # Calcul des rendements en évitant les divisions par zéro
                portfolio['returns'] = portfolio['total'].pct_change().fillna(0)
                
                # Calcul du ratio de Sharpe
                sharpe_ratio = self.calculate_sharpe_ratio(portfolio['returns'])
                
                # Calcul du drawdown maximum
                cumulative_returns = (1 + portfolio['returns']).cumprod()
                max_drawdown = self.calculate_max_drawdown(cumulative_returns)
                
                return {
                    'portfolio': portfolio,
                    'signals': signals,
                    'initial_capital': initial_capital,
                    'final_capital': portfolio['total'][-1],
                    'total_return': (portfolio['total'][-1] - initial_capital) / initial_capital,
                    'sharpe_ratio': sharpe_ratio if sharpe_ratio is not None else 0.0,
                    'max_drawdown': max_drawdown if max_drawdown is not None else 0.0
                }
        return None

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calcule le ratio de Sharpe"""
        if returns is not None and not returns.empty:
            excess_returns = returns - risk_free_rate/252  # Taux journalier
            if excess_returns.std() != 0:
                return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        return None

    def calculate_max_drawdown(self, cumulative_returns):
        """Calcule le drawdown maximum"""
        if cumulative_returns is not None and not cumulative_returns.empty:
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            return drawdown.min()
        return None 