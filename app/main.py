import streamlit as st
import pandas as pd
from services.trading_service import TradingService
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz
import json

# Fonction pour formater la monnaie
def format_currency(amount):
    return f"${amount:,.2f}"

# Fonction pour vérifier si le marché américain est ouvert
def is_market_open():
    # Définition des fuseaux horaires
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Vérifier si c'est le weekend
    if now.weekday() >= 5:  # 5 = Samedi, 6 = Dimanche
        return False, "Le marché est fermé (weekend)"
    
    # Vérifier l'heure (9:30 - 16:00 EST)
    market_open = now.replace(hour=9, minute=30, second=0)
    market_close = now.replace(hour=16, minute=0, second=0)
    
    if now < market_open:
        return False, f"Le marché ouvre dans {format_time_diff(now, market_open)}"
    elif now > market_close:
        next_open = market_open + timedelta(days=1)
        if now.weekday() == 4:  # Vendredi
            next_open = next_open + timedelta(days=2)  # Sauter le weekend
        return False, f"Le marché ouvre dans {format_time_diff(now, next_open)}"
    
    return True, f"Marché ouvert - Fermeture dans {format_time_diff(now, market_close)}"

# Fonction pour formater la différence de temps
def format_time_diff(t1, t2):
    diff = t2 - t1
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if diff.days > 0:
        return f"{diff.days}j {hours}h {minutes}m"
    else:
        return f"{hours}h {minutes}m"

# Initialisation du portefeuille dans la session si nécessaire
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {
        'cash': 10000.0,
        'holdings': {},
        'transactions': [],
        'history': []
    }

# Configuration de la page
st.set_page_config(
    page_title="Simulateur Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajouter une image d'arrière-plan et des styles CSS
st.markdown("""
<style>
    /* Styles de base */
    .main {
        background-color: #0f172a;
        color: #e2e8f0;
        overflow-x: hidden;
        overflow-y: auto;
    }
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-height: none;
        overflow: visible;
    }
    
    /* Bento Grid */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        grid-auto-rows: minmax(80px, auto);
        gap: 12px;
        margin: 0px;
        padding: 0 0 20px 0;
    }
    
    /* Cartes Bento */
    .bento-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        overflow: visible;
        position: relative;
        transition: all 0.3s ease;
    }
    .bento-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Tailles des cartes */
    .span-1 { grid-column: span 1; }
    .span-2 { grid-column: span 2; }
    .span-3 { grid-column: span 3; }
    .span-4 { grid-column: span 4; }
    .height-1 { 
        grid-row: span 1; 
        min-height: 150px;
    }
    .height-2 { 
        grid-row: span 2; 
        min-height: 300px;
    }
    .height-3 { 
        grid-row: span 3; 
        min-height: 450px;
    }
    .height-4 { 
        grid-row: span 4; 
        min-height: 600px;
    }
    
    /* Titres et textes */
    h1, h2, h3, h4 {
        color: #f8fafc;
        margin-top: 0;
    }
    .card-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-title-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #2563eb;
        border-radius: 6px;
        color: white;
    }
    
    /* Styles pour les métriques */
    .metric {
        display: flex;
        flex-direction: column;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
    }
    .metric-change {
        display: flex;
        align-items: center;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
    
    /* Styles pour les graphiques */
    .chart-container {
        width: 100%;
        height: 100%;
        min-height: 400px;
    }
    
    /* Configuration des graphiques Plotly */
    [data-testid="stPlotlyChart"] > div {
        width: 100% !important;
    }
    
    /* Style des graphiques responsifs */
    @media screen and (max-width: 1200px) {
        .bento-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .span-3 {
            grid-column: span 2;
        }
    }
    @media screen and (max-width: 768px) {
        .bento-grid {
            grid-template-columns: 1fr;
        }
        .span-1, .span-2, .span-3, .span-4 {
            grid-column: span 1;
        }
    }
    
    /* Styles pour les tableaux */
    .table-container {
        overflow: auto;
        max-height: 400px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #334155;
    }
    th {
        background-color: #1e293b;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    tr:hover {
        background-color: #1e3a8a15;
    }
    .badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-buy {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    /* Entrées et formulaires */
    input, select, .stButton>button {
        background-color: #334155 !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
    }
    .stButton>button {
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #1e40af !important;
        border-color: #1e40af !important;
    }
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #94a3b8 !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f8fafc !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    /* Masquer les éléments inutiles */
    footer, header, #MainMenu {
        display: none !important;
    }
    
    /* Header personnalisé */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .logo {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .logo-icon {
        width: 32px;
        height: 32px;
        background-color: #3b82f6;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    .logo-text {
        font-weight: 700;
        font-size: 1.5rem;
    }
    .market-status {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 12px;
        background-color: #1e293b;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    
    /* Sidebar */
    .sidebar .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# En-tête plus compact
st.markdown('<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><p class="logo-text">🚀 TradeSim</p><p class="description">Simulateur de trading en temps réel</p></div>', unsafe_allow_html=True)

# Sidebar réduite pour la configuration
with st.sidebar:
    # Logo et titre dans la sidebar
    st.markdown('<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;"><div class="logo-icon">📊</div><span style="font-weight: 700; font-size: 1.2rem;">TradeSim</span></div>', unsafe_allow_html=True)
    
    # Sélection du symbole
    st.markdown("<p style='margin: 0 0 5px 0; color: #94a3b8;'>Symbole</p>", unsafe_allow_html=True)
    symbol = st.text_input("", value="AAPL", help="Exemple: AAPL pour Apple, TSLA pour Tesla", label_visibility="collapsed")
    
    # Période
    st.markdown("<p style='margin: 10px 0 5px 0; color: #94a3b8;'>Période</p>", unsafe_allow_html=True)
    period = st.selectbox("", options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=1, label_visibility="collapsed")
    
    # Rafraîchissement
    st.markdown("<p style='margin: 10px 0 5px 0; color: #94a3b8;'>Rafraîchissement</p>", unsafe_allow_html=True)
    auto_refresh = st.checkbox("Auto", value=True)
    refresh_interval = st.slider("", min_value=5, max_value=60, value=15, label_visibility="collapsed")
    
    # Séparateur
    st.markdown("<hr style='margin: 20px 0; border-color: #334155;'>", unsafe_allow_html=True)
    
    # Portefeuille
    st.markdown("<p style='margin: 10px 0 5px 0; font-weight: 600; color: #f8fafc;'>Portefeuille</p>", unsafe_allow_html=True)
    
    # Calculer la valeur du portefeuille
    portfolio_value = st.session_state.portfolio['cash']
    for ticker, position in st.session_state.portfolio['holdings'].items():
        portfolio_value += position['quantity'] * position['avg_price']
    
    # Afficher la valeur et les liquidités
    initial_value = 10000.0
    pct_change = ((portfolio_value - initial_value) / initial_value) * 100
    change_color = "positive" if pct_change >= 0 else "negative"
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<p style='margin: 5px 0 0 0; color: #94a3b8;'>Valeur totale</p><p style='margin: 0; font-size: 1.1rem; font-weight: 600;'>{format_currency(portfolio_value)}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='margin: 5px 0 0 0; color: #94a3b8;'>Performance</p><p style='margin: 0; font-size: 1.1rem; font-weight: 600;' class='{change_color}'>{pct_change:+.2f}%</p>", unsafe_allow_html=True)
    
    st.markdown(f"<p style='margin: 15px 0 0 0; color: #94a3b8;'>Liquidités</p><p style='margin: 0; font-size: 1.1rem; font-weight: 600;'>{format_currency(st.session_state.portfolio['cash'])}</p>", unsafe_allow_html=True)
    
    # Positions
    if st.session_state.portfolio['holdings']:
        st.markdown("<p style='margin: 15px 0 5px 0; color: #94a3b8;'>Positions</p>", unsafe_allow_html=True)
        for ticker, position in st.session_state.portfolio['holdings'].items():
            position_value = position['quantity'] * position['avg_price']
            st.markdown(f"""
                <div style='background-color: #1e293b; padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span style='font-weight: 600;'>{ticker}</span>
                        <span>{format_currency(position_value)}</span>
                    </div>
                    <div style='display: flex; justify-content: space-between; font-size: 0.8rem; color: #94a3b8;'>
                        <span>{position['quantity']} actions</span>
                        <span>@{format_currency(position['avg_price'])}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Séparateur
    st.markdown("<hr style='margin: 20px 0; border-color: #334155;'>", unsafe_allow_html=True)

    # Bouton pour exporter les données
    st.markdown("<p style='margin: 10px 0 5px 0; font-weight: 600; color: #f8fafc;'>Exporter les données</p>", unsafe_allow_html=True)

    # Fonction pour générer le rapport au format JSON
    def generate_portfolio_report():
        report = {
            "portfolio_summary": {
                "cash": st.session_state.portfolio['cash'],
                "total_value": portfolio_value,
                "performance_percent": pct_change,
                "initial_investment": initial_value,
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "holdings": {},
            "transactions": []
        }
        
        # Ajouter les positions actuelles
        for ticker, position in st.session_state.portfolio['holdings'].items():
            report["holdings"][ticker] = {
                "quantity": position['quantity'],
                "avg_price": position['avg_price'],
                "current_value": position['quantity'] * position['avg_price']
            }
        
        # Ajouter les transactions
        for transaction in st.session_state.portfolio['transactions']:
            report["transactions"].append({
                "date": transaction['timestamp'],
                "symbol": transaction['symbol'],
                "type": transaction['type'],
                "quantity": transaction['quantity'],
                "price": transaction['price'],
                "total": transaction['total']
            })
        
        return report

    # Bouton pour exporter
    if st.button("Exporter pour analyse", type="primary"):
        report = generate_portfolio_report()
        report_json = json.dumps(report, indent=2)
        st.code(report_json, language="json")
        st.download_button(
            label="Télécharger le rapport",
            data=report_json,
            file_name=f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
        st.info("Copiez ce JSON et partagez-le avec ChatGPT pour obtenir des conseils d'investissement personnalisés.")

# Obtenir le statut du marché
market_open, market_status = is_market_open()
status_color = "green" if market_open else "orange"

# En-tête du dashboard
st.markdown(f"""
<div class="header">
    <div class="logo">
        <div class="logo-icon">📈</div>
        <div class="logo-text">TradeSim Dashboard</div>
    </div>
    <div class="market-status">
        <div class="status-dot" style="background-color: {status_color};"></div>
        <span>{market_status}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Conteneur principal avec la grille Bento
st.markdown('<div class="bento-grid">', unsafe_allow_html=True)

# Placeholder pour les éléments dynamiques
metrics_placeholder = st.empty()
stock_info_placeholder = st.empty()
chart_placeholder = st.empty()
order_form_placeholder = st.empty()
transactions_placeholder = st.empty()
performance_placeholder = st.empty()

st.markdown('</div>', unsafe_allow_html=True)

# Fonction pour mettre à jour le portefeuille
def update_portfolio(symbol, price, quantity, trade_type):
    # Vérifier si le marché est ouvert
    market_open, market_status = is_market_open()
    
    if not market_open:
        st.error(f"Transaction impossible: {market_status}")
        return False
    
    portfolio = st.session_state.portfolio
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if trade_type == "Achat":
        cost = price * quantity
        
        # Vérifier si l'utilisateur a assez de liquidités
        if cost > portfolio['cash']:
            st.error("Liquidités insuffisantes pour cette transaction")
            return False
        
        # Mettre à jour les liquidités
        portfolio['cash'] -= cost
        
        # Mettre à jour les positions
        if symbol in portfolio['holdings']:
            # Mettre à jour une position existante
            current_position = portfolio['holdings'][symbol]
            total_quantity = current_position['quantity'] + quantity
            total_cost = (current_position['quantity'] * current_position['avg_price']) + cost
            current_position['quantity'] = total_quantity
            current_position['avg_price'] = total_cost / total_quantity
        else:
            # Créer une nouvelle position
            portfolio['holdings'][symbol] = {
                'quantity': quantity,
                'avg_price': price
            }
        
        # Ajouter la transaction à l'historique
        portfolio['transactions'].append({
            'timestamp': timestamp,
            'symbol': symbol,
            'type': 'BUY',
            'quantity': quantity,
            'price': price,
            'total': cost
        })
        
        st.success(f"Achat de {quantity} {symbol} à ${price:.2f}")
        
    elif trade_type == "Vente":
        # Vérifier si l'utilisateur possède assez d'actions
        if symbol not in portfolio['holdings'] or portfolio['holdings'][symbol]['quantity'] < quantity:
            st.error("Vous ne possédez pas assez d'actions pour cette vente")
            return False
        
        # Calculer le produit de la vente
        proceeds = price * quantity
        
        # Mettre à jour les liquidités
        portfolio['cash'] += proceeds
        
        # Mettre à jour les positions
        portfolio['holdings'][symbol]['quantity'] -= quantity
        
        # Supprimer la position si plus d'actions
        if portfolio['holdings'][symbol]['quantity'] == 0:
            del portfolio['holdings'][symbol]
        
        # Ajouter la transaction à l'historique
        portfolio['transactions'].append({
            'timestamp': timestamp,
            'symbol': symbol,
            'type': 'SELL',
            'quantity': quantity,
            'price': price,
            'total': proceeds
        })
        
        st.success(f"Vente de {quantity} {symbol} à ${price:.2f}")
    
    # Enregistrer la valeur totale du portefeuille pour l'historique
    total_value = portfolio['cash']
    for sym, pos in portfolio['holdings'].items():
        # Ici, on devrait idéalement utiliser le prix actuel de chaque action
        # Mais pour simplifier, on utilise le prix moyen d'achat
        total_value += pos['quantity'] * pos['avg_price']
    
    portfolio['history'].append({
        'timestamp': timestamp,
        'total_value': total_value
    })
    
    return True

# Initialisation du service de trading
trading_service = None
last_price = None
last_update = None

while True:
    try:
        # Chargement des données
        with st.spinner("Chargement des données..."):
            trading_service = TradingService(symbol, period)
        
        if trading_service.data is None:
            st.error(f"""
                Impossible de charger les données pour {symbol}.
                Veuillez vérifier :
                - Le symbole est correct
                - La période sélectionnée
                - Votre connexion internet
            """)
            break
            
        if len(trading_service.data) < 2:
            st.warning(f"Pas assez de données pour {symbol}. Essayez une période plus longue.")
            break
            
        # Prix et variation actuels
        current_price = trading_service.data['Close'].iloc[-1]
        price_change = trading_service.data['Close'].pct_change().iloc[-1] * 100
        price_change_icon = "📈" if price_change >= 0 else "📉"
        price_change_class = "positive" if price_change >= 0 else "negative"
        
        # Mise à jour des données
        last_price = current_price
        last_update = datetime.now()
        
        # 1. MÉTRIQUES PRINCIPALES
        with metrics_placeholder.container():
            st.markdown(f"""
            <div class="bento-card span-4 height-1">
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
                    <div class="metric">
                        <div class="metric-label">Prix actuel</div>
                        <div class="metric-value">{format_currency(current_price)}</div>
                        <div class="metric-change {price_change_class}">{price_change_icon} {price_change:+.2f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Volume</div>
                        <div class="metric-value">{int(trading_service.data['Volume'].iloc[-1]):,}</div>
                        <div class="metric-label">dernières 24h</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Haut/Bas du jour</div>
                        <div class="metric-value">{format_currency(trading_service.data['High'].iloc[-1])}</div>
                        <div class="metric-label">{format_currency(trading_service.data['Low'].iloc[-1])}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Mise à jour</div>
                        <div class="metric-value">{datetime.now().strftime("%H:%M:%S")}</div>
                        <div class="metric-label">Rafraîchissement: {'On' if auto_refresh else 'Off'}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 2. GRAPHIQUE PRINCIPAL
        # Préparer le graphique en chandeliers
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=trading_service.data.index,
            open=trading_service.data['Open'],
            high=trading_service.data['High'],
            low=trading_service.data['Low'],
            close=trading_service.data['Close'],
            name=symbol,
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ))
        
        # Ajouter les transactions au graphique
        for transaction in st.session_state.portfolio['transactions']:
            transaction_time = datetime.strptime(transaction['timestamp'], "%Y-%m-%d %H:%M:%S")
            if transaction_time >= trading_service.data.index[0] and transaction['symbol'] == symbol:
                marker_color = '#10b981' if transaction['type'] == 'BUY' else '#ef4444'
                marker_symbol = 'triangle-up' if transaction['type'] == 'BUY' else 'triangle-down'
                
                fig.add_trace(go.Scatter(
                    x=[transaction_time],
                    y=[transaction['price']],
                    mode='markers',
                    name=f"{transaction['type']} {transaction['quantity']}",
                    marker=dict(
                        symbol=marker_symbol,
                        size=15,
                        color=marker_color,
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate=f"<b>{transaction['type']}</b><br>" +
                                  f"Prix: {format_currency(transaction['price'])}<br>" +
                                  f"Quantité: {transaction['quantity']}<br>" +
                                  f"Total: {format_currency(transaction['total'])}"
                ))
        
        # Style du graphique
        fig.update_layout(
            title=None,
            height=450,
            autosize=True,
            template="plotly_dark",
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                rangeslider=dict(visible=True, bgcolor='#334155', thickness=0.05),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1j", step="day", stepmode="backward"),
                        dict(count=7, label="1s", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(step="all", label="Tout")
                    ]),
                    bgcolor='#334155',
                    activecolor='#1e40af'
                )
            )
        )
        
        with chart_placeholder.container():
            st.markdown('<div class="bento-card span-3 height-3">', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="card-title">
                    <span>{symbol} - Graphique des prix</span>
                    <div class="card-title-icon">{price_change_icon}</div>
                </div>
                <div style="width:100%; height:450px;">
            """, unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'responsive': True})
            st.markdown('</div></div>', unsafe_allow_html=True)
        
        # 3. INFORMATIONS SUR L'ACTION
        # Obtenir un nom d'entreprise pour le symbole
        company_name = "Apple Inc." if symbol == "AAPL" else symbol
        
        # Préparer une mini-tendance
        mini_fig = go.Figure()
        mini_fig.add_trace(go.Scatter(
            x=trading_service.data.index[-20:],
            y=trading_service.data['Close'][-20:],
            line=dict(color='#4f46e5', width=2),
            fill='tozeroy',
            fillcolor='rgba(79, 70, 229, 0.1)'
        ))
        
        mini_fig.update_layout(
            height=120,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False)
        )
        
        with stock_info_placeholder.container():
            st.markdown(f"""
            <div class="bento-card span-1 height-2">
                <div class="card-title">
                    <span>{symbol}</span>
                    <div class="card-title-icon">ℹ️</div>
                </div>
                <p style="font-size: 1.1rem; margin: 0 0 15px 0;">{company_name}</p>
            """, unsafe_allow_html=True)
            
            st.plotly_chart(mini_fig, use_container_width=True, config={'displayModeBar': False})
            
            # Calculer quelques métriques supplémentaires
            avg_price = trading_service.data['Close'].mean()
            max_price = trading_service.data['High'].max()
            trend = "Haussière" if price_change >= 0 else "Baissière"
            trend_color = "#10b981" if price_change >= 0 else "#ef4444"
            
            st.markdown(f"""
                <div style="margin-top: 15px;">
                    <table style="width: 100%; font-size: 0.9rem;">
                        <tr>
                            <td style="color: #94a3b8;">Ouverture</td>
                            <td style="text-align: right;">{format_currency(trading_service.data['Open'].iloc[-1])}</td>
                        </tr>
                        <tr>
                            <td style="color: #94a3b8;">Haut</td>
                            <td style="text-align: right;">{format_currency(trading_service.data['High'].iloc[-1])}</td>
                        </tr>
                        <tr>
                            <td style="color: #94a3b8;">Bas</td>
                            <td style="text-align: right;">{format_currency(trading_service.data['Low'].iloc[-1])}</td>
                        </tr>
                        <tr>
                            <td style="color: #94a3b8;">Prix moyen</td>
                            <td style="text-align: right;">{format_currency(avg_price)}</td>
                        </tr>
                        <tr>
                            <td style="color: #94a3b8;">Maximum</td>
                            <td style="text-align: right;">{format_currency(max_price)}</td>
                        </tr>
                        <tr>
                            <td style="color: #94a3b8;">Tendance</td>
                            <td style="text-align: right; color: {trend_color};">{trend}</td>
                        </tr>
                    </table>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 4. FORMULAIRE DE PASSAGE D'ORDRE
        with order_form_placeholder.container():
            st.markdown(f"""
            <div class="bento-card span-1 height-1">
                <div class="card-title">
                    <span>Passer un ordre</span>
                    <div class="card-title-icon">📋</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Formulaire pour passer un ordre
            with st.form("trade_form", clear_on_submit=False):
                cols = st.columns([1, 1])
                with cols[0]:
                    st.markdown("<p style='margin: 0 0 5px 0; color: #94a3b8;'>Type</p>", unsafe_allow_html=True)
                    trade_type = st.radio(
                        "",
                        ["Achat", "Vente"], 
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                
                with cols[1]:
                    st.markdown("<p style='margin: 0 0 5px 0; color: #94a3b8;'>Quantité</p>", unsafe_allow_html=True)
                    quantity = st.number_input("", min_value=1, value=1, step=1, label_visibility="collapsed")
                
                # Valeur estimée
                est_value = format_currency(quantity * current_price) if current_price else "-- --"
                st.markdown(f"<p style='color: #94a3b8; margin: 10px 0 5px 0;'>Valeur estimée: <span style='color: #f8fafc;'>{est_value}</span></p>", unsafe_allow_html=True)
                
                # Bouton selon le type d'ordre
                button_text = trade_type
                button_color = "primary" if trade_type == "Achat" else "secondary"
                
                # Statut du marché pour le bouton
                button_disabled = not market_open
                
                submit_button = st.form_submit_button(
                    button_text, 
                    type=button_color,
                    disabled=button_disabled,
                    use_container_width=True
                )
                
                if not market_open:
                    st.markdown("<p style='color: #f87171; font-size: 0.8rem; margin: 5px 0 0 0;'>Marché fermé</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 5. HISTORIQUE DES TRANSACTIONS
        with transactions_placeholder.container():
            st.markdown(f"""
            <div class="bento-card span-1 height-2">
                <div class="card-title">
                    <span>Transactions récentes</span>
                    <div class="card-title-icon">🔄</div>
                </div>
                <div class="table-container">
            """, unsafe_allow_html=True)
            
            if st.session_state.portfolio['transactions']:
                transactions_df = pd.DataFrame(st.session_state.portfolio['transactions'][-10:])
                transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
                transactions_df = transactions_df.sort_values('timestamp', ascending=False)
                
                # Créer un tableau HTML stylisé
                html_table = "<table style='width: 100%;'>"
                
                # En-tête du tableau
                html_table += """
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Qté</th>
                    <th>Prix</th>
                </tr>
                """
                
                # Lignes du tableau
                for i, row in transactions_df.iterrows():
                    badge_class = "badge-buy" if row['type'] == "BUY" else "badge-sell"
                    badge_text = "ACHAT" if row['type'] == "BUY" else "VENTE"
                    
                    html_table += f"""
                    <tr>
                        <td>{row['timestamp'].strftime('%d/%m %H:%M')}</td>
                        <td><span class="badge {badge_class}">{badge_text}</span></td>
                        <td>{row['quantity']}</td>
                        <td>{format_currency(row['price'])}</td>
                    </tr>
                    """
                
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #94a3b8; text-align: center; margin-top: 30px;'>Aucune transaction</p>", unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        # 6. PERFORMANCE DU PORTEFEUILLE
        with performance_placeholder.container():
            st.markdown(f"""
            <div class="bento-card span-4 height-1">
                <div class="card-title">
                    <span>Performance du portefeuille</span>
                    <div class="card-title-icon">📊</div>
                </div>
            """, unsafe_allow_html=True)
            
            if len(st.session_state.portfolio['history']) > 0:
                # Préparer les données pour le graphique de performance
                history_df = pd.DataFrame(st.session_state.portfolio['history'])
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                
                # Créer le graphique
                perf_fig = go.Figure()
                perf_fig.add_trace(go.Scatter(
                    x=history_df['timestamp'],
                    y=history_df['total_value'],
                    name='Valeur du portefeuille',
                    line=dict(color='#4f46e5', width=2)
                ))
                
                # Ajouter une ligne de référence pour le capital initial
                perf_fig.add_hline(
                    y=10000, 
                    line=dict(color='gray', dash='dash'),
                    annotation_text="Capital initial"
                )
                
                # Styling
                perf_fig.update_layout(
                    height=180,
                    autosize=True,
                    template="plotly_dark",
                    plot_bgcolor='#1e293b',
                    paper_bgcolor='#1e293b',
                    font=dict(color='#e2e8f0'),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False, tickformat='$,.0f')
                )
                
                st.plotly_chart(perf_fig, use_container_width=True, config={'displayModeBar': False, 'responsive': True})
            else:
                st.markdown("<p style='color: #94a3b8; text-align: center; margin: 50px 0;'>Effectuez des transactions pour voir l'évolution de votre portefeuille</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Traitement du formulaire
        if submit_button:
            update_portfolio(symbol, current_price, quantity, trade_type)
        
        # Attendre avant de mettre à jour
        if not auto_refresh:
            break
            
        time.sleep(refresh_interval)
        
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour : {str(e)}")
        break 