# MultiTool - Ethical Hacking Utility

**MultiTool** est une application développée en Python par Guy Kouakou (KAGEHACKER) dans le cadre de mes études en hacking éthique et développement logiciel. Cet outil combine deux fonctionnalités principales : un convertisseur de devises et un raccourcisseur d’URL, avec une interface graphique moderne et intuitive construite avec Tkinter.

## Fonctionnalités

- **Convertisseur de Devises** :
  - Convertit des montants entre différentes devises en temps réel via l’API `exchangerate-api.com`.
  - Historique des conversions avec recherche et exportation au format CSV.
  - Affichage des tendances (placeholder pour une future intégration d’API de données historiques).

- **Raccourcisseur d’URL** :
  - Raccourcit les URL via l’API `tinyurl.com`.
  - Option pour copier l’URL raccourcie dans le presse-papiers.
  - Analyse de sécurité (placeholder pour une intégration future avec Google Safe Browsing).

- **Interface Utilisateur** :
  - Thèmes clair et sombre basculables.
  - Animation de la signature en bas de l’écran.
  - Mode plein écran activable avec la touche `F11`.

- **Sécurité** :
  - Historique chiffré avec la bibliothèque `cryptography`.
  - Gestion robuste des erreurs avec journalisation dans `multitool.log`.

## Prérequis

- **Python 3.7+**
- Dépendances :
  - `requests`
  - `pyperclip`
  - `pillow`
  - `matplotlib`
  - `cryptography`

Installez les dépendances avec :
```bash
pip install -r requirements.txt
