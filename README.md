# TradeSim - Simulateur de Trading en Temps Réel

![TradeSim Dashboard](docs/screenshot.png)

TradeSim est un simulateur de trading interactif développé en Python qui permet aux utilisateurs de s'entraîner au trading sans risquer de l'argent réel. L'application offre une interface moderne et en temps réel pour simuler l'achat et la vente d'actions sur les marchés financiers.

## Fonctionnalités

- **Données en temps réel** : Affichage des prix actuels des actions via Yahoo Finance
- **Interface interactive** : Dashboard moderne avec graphiques et indicateurs
- **Portefeuille virtuel** : Suivi de vos investissements virtuels
- **Analyse technique** : Visualisation des graphiques en chandeliers
- **Simulateur de marché** : Tient compte des heures d'ouverture du marché
- **Exportation des données** : Exportez vos transactions pour analyse

## Technologies utilisées

- **Backend** : Python, Yahoo Finance API
- **Frontend** : Streamlit
- **Visualisation** : Plotly
- **Analyse de données** : Pandas, NumPy

## Installation

1. Clonez ce dépôt
   ```
   git clone https://github.com/votre-utilisateur/tradesim.git
   cd tradesim
   ```

2. Installez les dépendances
   ```
   pip install -r requirements.txt
   ```

3. Lancez l'application
   ```
   python -m streamlit run app/main.py
   ```

## Utilisation

1. Saisissez le symbole de l'action que vous souhaitez trader (ex: AAPL, TSLA)
2. Sélectionnez la période d'analyse
3. Utilisez le formulaire de passage d'ordre pour acheter ou vendre des actions
4. Suivez la performance de votre portefeuille

## Exportation pour analyse

L'application vous permet d'exporter l'historique de vos transactions et la composition de votre portefeuille au format JSON. Vous pouvez ensuite utiliser ces données avec des outils d'IA comme ChatGPT pour obtenir des conseils personnalisés sur votre stratégie de trading.

## Captures d'écran

![TradeSim Interface](docs/dashboard.png)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails. 