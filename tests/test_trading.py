import pytest
from app.services.trading_service import TradingService

def test_trading_service_initialization():
    """Test l'initialisation du service de trading"""
    service = TradingService("AAPL")
    assert service.symbol == "AAPL"
    assert service.period == "1y"
    assert service.data is not None

def test_calculate_sma():
    """Test le calcul de la moyenne mobile simple"""
    service = TradingService("AAPL")
    sma = service.calculate_sma(window=20)
    assert sma is not None
    assert len(sma) > 0

def test_calculate_rsi():
    """Test le calcul du RSI"""
    service = TradingService("AAPL")
    rsi = service.calculate_rsi(window=14)
    assert rsi is not None
    assert len(rsi) > 0
    assert all(0 <= x <= 100 for x in rsi.dropna())

def test_calculate_bollinger_bands():
    """Test le calcul des bandes de Bollinger"""
    service = TradingService("AAPL")
    bb = service.calculate_bollinger_bands()
    assert bb is not None
    assert 'upper' in bb
    assert 'middle' in bb
    assert 'lower' in bb
    assert len(bb['upper']) > 0

def test_sharpe_ratio():
    """Test le calcul du ratio de Sharpe"""
    service = TradingService("AAPL")
    # Créer des rendements factices pour le test
    returns = service.data['Close'].pct_change()
    sharpe = service.calculate_sharpe_ratio(returns)
    assert sharpe is not None
    assert isinstance(sharpe, float)

def test_max_drawdown():
    """Test le calcul du drawdown maximum"""
    service = TradingService("AAPL")
    # Créer des rendements cumulatifs factices pour le test
    returns = service.data['Close'].pct_change()
    cumulative_returns = (1 + returns).cumprod()
    max_drawdown = service.calculate_max_drawdown(cumulative_returns)
    assert max_drawdown is not None
    assert isinstance(max_drawdown, float)
    assert max_drawdown <= 0 