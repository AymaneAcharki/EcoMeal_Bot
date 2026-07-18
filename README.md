

# 🌱 EcoMeal Bot

> **FR** — Assistant culinaire intelligent pour découvrir des recettes plus durables, estimer leur empreinte carbone et organiser les repas.  
> **EN** — Intelligent cooking assistant for discovering more sustainable recipes, estimating their carbon footprint and planning meals.

<p align="center">
  <a href="#francais">
    <img src="https://img.shields.io/badge/Lire_en-Français-0055A4?style=for-the-badge" alt="Lire en français">
  </a>
  <a href="#english">
    <img src="https://img.shields.io/badge/Read_in-English-C8102E?style=for-the-badge" alt="Read in English">
  </a>
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/AymaneAshrk/EcoMeal_Bot">
    <img src="https://img.shields.io/badge/Try_the-Live_Demo-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Try the live demo">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/LLM-Hugging%20Face%20%7C%20LM%20Studio-yellow.svg" alt="LLM providers">
  <img src="https://img.shields.io/badge/SDG-12%20Responsible%20Consumption-4C9F38.svg" alt="UN SDG 12">
</p>

---

<a id="francais"></a>

## 🇫🇷 Version française

> La version anglaise est disponible plus bas dans ce document.

### 📋 Table des matières

- [Aperçu](#-aperçu)
- [Contexte académique](#-contexte-académique)
- [Fonctionnalités](#-fonctionnalités)
- [Fonctionnement](#-fonctionnement)
- [Structure du projet](#-structure-du-projet)
- [Installation et exécution](#-installation-et-exécution)
- [Configuration des modèles](#-configuration-des-modèles)
- [Données environnementales](#-données-environnementales)
- [Déploiement](#-déploiement)
- [Limites](#-limites)
- [Licence](#-licence)

---

### 🎯 Aperçu

EcoMeal Bot est une application Streamlit conçue pour aider les utilisateurs à adopter une alimentation plus durable.

L’application combine une base de plus de 2 000 recettes, des données environnementales et un modèle de langage afin de :

- proposer des recettes adaptées aux ingrédients disponibles ;
- prendre en compte les préférences alimentaires ;
- estimer l’empreinte carbone d’un repas ;
- suggérer des substitutions plus durables ;
- produire des listes de courses ;
- générer des plans de repas ;
- conserver les profils et l’historique des conversations.

L’interface comprend quatre espaces principaux :

- **Home** : présentation et accès rapide aux fonctionnalités ;
- **Chat** : interaction avec l’assistant culinaire ;
- **Profile** : gestion des préférences et contraintes ;
- **Analysis** : suivi et analyse des indicateurs d’utilisation et d’impact.

---

### 🎓 Contexte académique

EcoMeal a été initialement développé dans le cadre d’un **projet de groupe** pour le cours **Artificial Intelligence and SDG**, au second semestre du **MSc 2 Data Analytics for Business à KEDGE Business School** (2025–2026).

**Note du projet de groupe : 16,7/20.**

Ce dépôt contient l’application consolidée ainsi que les améliorations réalisées ultérieurement pour :

- renforcer l’architecture du projet ;
- améliorer l’expérience utilisateur ;
- permettre un fonctionnement local ou cloud ;
- déployer l’application sur Hugging Face Spaces ;
- automatiser la synchronisation entre GitHub et Hugging Face ;
- préparer le projet pour une présentation portfolio.

---

### ✨ Fonctionnalités

#### Assistant culinaire

- recherche de recettes à partir d’ingrédients ;
- compréhension de demandes en langage naturel ;
- modification d’une recette existante ;
- génération guidée de recettes ;
- recommandations adaptées au profil utilisateur.

#### Durabilité

- estimation des émissions de CO₂ par ingrédient et par repas ;
- classification de l’impact environnemental ;
- comparaison avec une référence moyenne ;
- prise en compte de la saisonnalité ;
- multiplicateurs environnementaux selon le pays ;
- propositions de substitutions moins carbonées.

#### Organisation

- création de listes de courses ;
- planification de repas ;
- estimation budgétaire ;
- gestion de plusieurs devises ;
- adaptation à la taille du foyer.

#### Personnalisation

- profils utilisateurs ;
- préférences alimentaires ;
- allergies et exclusions ;
- budget hebdomadaire ;
- pays et devise ;
- durée maximale de préparation ;
- historique des conversations.

#### Intelligence artificielle

Deux modes sont pris en charge :

- **Hugging Face Inference API** pour l’utilisation cloud ;
- **LM Studio** pour l’exécution locale d’un modèle compatible OpenAI.

---

### ⚙️ Fonctionnement

Le flux principal est le suivant :

```text
Demande utilisateur
        ↓
Analyse de l’intention
        ↓
Chargement du profil et des préférences
        ↓
Recherche dans la base de recettes
        ↓
Génération ou adaptation par le LLM
        ↓
Calcul CO₂, budget et substitutions
        ↓
Affichage de la recette et actions associées
```

Les fonctions déterministes — recherche, calcul carbone, budget, profils et listes de courses — sont séparées de la génération effectuée par le modèle de langage.

---

### 📁 Structure du projet

```text
EcoMeal_Bot/
├── app.py
├── config.py
├── run.py
├── requirements.txt
├── chat/
│   ├── engine.py
│   ├── prompts.py
│   ├── parser.py
│   ├── history.py
│   └── conversation_manager.py
├── core/
│   ├── co2.py
│   ├── ingredients.py
│   ├── recipe_search.py
│   ├── shopping.py
│   ├── budget.py
│   ├── substitutions.py
│   └── carbon_tracker.py
├── profile/
│   ├── models.py
│   ├── manager.py
│   └── defaults.py
├── ui/
│   ├── styles.py
│   ├── sidebar.py
│   ├── chat_area.py
│   ├── recipe_card.py
│   ├── shopping_list.py
│   ├── welcome_tab.py
│   ├── profile_tab.py
│   └── analysis_tab.py
└── data/
    ├── aliments.json
    ├── prices.json
    ├── seasons.json
    ├── country_co2.json
    ├── emblematic_recipes.json
    ├── recipes/
    │   └── recipes_db.json
    ├── profiles/
    └── conversations/
```

---

### 🚀 Installation et exécution

#### Prérequis

- Python 3.10 ou supérieur ;
- `pip` ;
- un token Hugging Face pour le mode cloud, ou LM Studio pour le mode local.

#### Installation

```bash
git clone https://github.com/AymaneAcharki/EcoMeal_Bot.git
cd EcoMeal_Bot

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

#### Option A — Hugging Face

Définir les variables d’environnement :

```bash
export LLM_PROVIDER=huggingface
export HF_API_TOKEN=hf_your_token_here
```

Puis lancer :

```bash
streamlit run app.py
```

Le modèle cloud par défaut est :

```text
meta-llama/Llama-3.2-1B-Instruct
```

#### Option B — LM Studio

1. installer et ouvrir LM Studio ;
2. charger un modèle compatible ;
3. démarrer le serveur local sur le port `1234` ;
4. définir les variables :

```bash
export LLM_PROVIDER=lm_studio
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_MODEL=qwen3.5:0.8b
```

5. lancer l’application :

```bash
streamlit run app.py
```

---

### 🤖 Configuration des modèles

Les paramètres principaux se trouvent dans `config.py`.

| Paramètre | Valeur par défaut |
|---|---|
| Fournisseur | `huggingface` |
| Modèle Hugging Face | `meta-llama/Llama-3.2-1B-Instruct` |
| URL LM Studio | `http://localhost:1234/v1` |
| Modèle LM Studio | `qwen3.5:0.8b` |
| Température | `0.3` |
| Top-p | `0.95` |
| Repeat penalty | `1.1` |

Les modèles peuvent être remplacés à l’aide des variables d’environnement correspondantes.

---

### 🌍 Données environnementales

Le projet utilise plusieurs sources et référentiels pour structurer les estimations environnementales :

- ADEME ;
- base Agribalyse ;
- facteurs d’émission associés aux aliments ;
- données de saisonnalité ;
- multiplicateurs carbone par pays ;
- facteurs liés aux réseaux électriques.

Les valeurs produites constituent des **estimations d’aide à la décision**. Elles ne doivent pas être considérées comme des analyses de cycle de vie certifiées pour chaque recette.

---

### ☁️ Déploiement

L’application est accessible sur Hugging Face Spaces :

[![Tester EcoMeal Bot](https://img.shields.io/badge/Tester-EcoMeal_Bot-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/AymaneAshrk/EcoMeal_Bot)

La branche GitHub `main` constitue la source de référence. Un workflow GitHub Actions synchronise automatiquement chaque nouveau push vers le dépôt Hugging Face Space.

Deux secrets distincts sont utilisés :

- `HF_TOKEN` dans GitHub Actions pour autoriser le déploiement ;
- `HF_API_TOKEN` dans Hugging Face Spaces pour permettre l’inférence du modèle.

---

### ⚠️ Limites

- les estimations de CO₂ dépendent de la qualité et de la granularité des facteurs disponibles ;
- les réponses générées peuvent varier selon le modèle utilisé ;
- le modèle peut produire une recette nécessitant une validation humaine ;
- les données de prix et de saisonnalité peuvent devenir obsolètes ;
- l’application ne remplace pas un avis nutritionnel ou médical ;
- le stockage local des profils et conversations n’est pas conçu comme une base multi-utilisateur de production.

---

### 📄 Licence

Ce projet est distribué sous licence MIT. Voir le fichier [`LICENSE`](LICENSE).

<p align="right"><a href="#top">⬆ Retour en haut</a></p>

---

<a id="english"></a>

## 🇬🇧 English version

> The French version is available above in this document.

### 📋 Table of contents

- [Overview](#-overview)
- [Academic context](#-academic-context)
- [Features](#-features)
- [How it works](#-how-it-works)
- [Project structure](#-project-structure)
- [Installation and execution](#-installation-and-execution)
- [Model configuration](#-model-configuration)
- [Environmental data](#-environmental-data)
- [Deployment](#-deployment)
- [Limitations](#-limitations)
- [License](#-license)

---

### 🎯 Overview

EcoMeal Bot is a Streamlit application designed to help users adopt more sustainable eating habits.

The application combines a database of more than 2,000 recipes, environmental data and a language model to:

- recommend recipes based on available ingredients;
- account for dietary preferences;
- estimate the carbon footprint of a meal;
- suggest more sustainable substitutions;
- generate shopping lists;
- create meal plans;
- preserve user profiles and conversation history.

The interface contains four main areas:

- **Home**: introduction and quick access to features;
- **Chat**: interaction with the cooking assistant;
- **Profile**: management of preferences and constraints;
- **Analysis**: monitoring and analysis of usage and impact indicators.

---

### 🎓 Academic context

EcoMeal was originally developed as a **group project** for the **Artificial Intelligence and SDG** course during Semester 2 of the **MSc 2 Data Analytics for Business at KEDGE Business School** (2025–2026).

**Group project grade: 16.7/20.**

This repository contains the consolidated application and the subsequent improvements made to:

- strengthen the project architecture;
- improve the user experience;
- support both local and cloud execution;
- deploy the application on Hugging Face Spaces;
- automate synchronization between GitHub and Hugging Face;
- prepare the project for portfolio presentation.

---

### ✨ Features

#### Cooking assistant

- recipe search based on ingredients;
- natural-language request understanding;
- modification of existing recipes;
- guided recipe generation;
- recommendations adapted to the user profile.

#### Sustainability

- CO₂ estimation by ingredient and meal;
- environmental-impact classification;
- comparison with an average reference;
- seasonal-availability support;
- country-specific environmental multipliers;
- lower-carbon ingredient substitutions.

#### Organization

- shopping-list generation;
- meal planning;
- budget estimation;
- multi-currency support;
- household-size adaptation.

#### Personalization

- user profiles;
- dietary preferences;
- allergies and exclusions;
- weekly budget;
- country and currency;
- maximum cooking time;
- conversation history.

#### Artificial intelligence

Two execution modes are supported:

- **Hugging Face Inference API** for cloud usage;
- **LM Studio** for running a local OpenAI-compatible model.

---

### ⚙️ How it works

The main flow is:

```text
User request
      ↓
Intent analysis
      ↓
Profile and preference loading
      ↓
Recipe database search
      ↓
LLM generation or adaptation
      ↓
CO₂, budget and substitution calculations
      ↓
Recipe display and related actions
```

Deterministic functions — search, carbon calculations, budgets, profiles and shopping lists — are separated from language-model generation.

---

### 📁 Project structure

```text
EcoMeal_Bot/
├── app.py
├── config.py
├── run.py
├── requirements.txt
├── chat/
│   ├── engine.py
│   ├── prompts.py
│   ├── parser.py
│   ├── history.py
│   └── conversation_manager.py
├── core/
│   ├── co2.py
│   ├── ingredients.py
│   ├── recipe_search.py
│   ├── shopping.py
│   ├── budget.py
│   ├── substitutions.py
│   └── carbon_tracker.py
├── profile/
│   ├── models.py
│   ├── manager.py
│   └── defaults.py
├── ui/
│   ├── styles.py
│   ├── sidebar.py
│   ├── chat_area.py
│   ├── recipe_card.py
│   ├── shopping_list.py
│   ├── welcome_tab.py
│   ├── profile_tab.py
│   └── analysis_tab.py
└── data/
    ├── aliments.json
    ├── prices.json
    ├── seasons.json
    ├── country_co2.json
    ├── emblematic_recipes.json
    ├── recipes/
    │   └── recipes_db.json
    ├── profiles/
    └── conversations/
```

---

### 🚀 Installation and execution

#### Requirements

- Python 3.10 or newer;
- `pip`;
- a Hugging Face token for cloud mode, or LM Studio for local mode.

#### Installation

```bash
git clone https://github.com/AymaneAcharki/EcoMeal_Bot.git
cd EcoMeal_Bot

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

#### Option A — Hugging Face

Set the environment variables:

```bash
export LLM_PROVIDER=huggingface
export HF_API_TOKEN=hf_your_token_here
```

Then run:

```bash
streamlit run app.py
```

The default cloud model is:

```text
meta-llama/Llama-3.2-1B-Instruct
```

#### Option B — LM Studio

1. install and open LM Studio;
2. load a compatible model;
3. start the local server on port `1234`;
4. set the variables:

```bash
export LLM_PROVIDER=lm_studio
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_MODEL=qwen3.5:0.8b
```

5. start the application:

```bash
streamlit run app.py
```

---

### 🤖 Model configuration

The main settings are defined in `config.py`.

| Setting | Default value |
|---|---|
| Provider | `huggingface` |
| Hugging Face model | `meta-llama/Llama-3.2-1B-Instruct` |
| LM Studio URL | `http://localhost:1234/v1` |
| LM Studio model | `qwen3.5:0.8b` |
| Temperature | `0.3` |
| Top-p | `0.95` |
| Repeat penalty | `1.1` |

Models can be replaced through the corresponding environment variables.

---

### 🌍 Environmental data

The project uses several sources and reference datasets to structure its environmental estimates:

- ADEME;
- Agribalyse database;
- food-related emission factors;
- seasonal-availability data;
- country-level carbon multipliers;
- electricity-grid factors.

The resulting values are **decision-support estimates** and should not be interpreted as certified lifecycle assessments for individual recipes.

---

### ☁️ Deployment

The application is available on Hugging Face Spaces:

[![Try EcoMeal Bot](https://img.shields.io/badge/Try-EcoMeal_Bot-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/AymaneAshrk/EcoMeal_Bot)

The GitHub `main` branch is the source of truth. A GitHub Actions workflow automatically synchronizes every new push with the Hugging Face Space repository.

Two separate secrets are used:

- `HF_TOKEN` in GitHub Actions to authorize deployment;
- `HF_API_TOKEN` in Hugging Face Spaces to enable model inference.

---

### ⚠️ Limitations

- CO₂ estimates depend on the quality and granularity of the available factors;
- generated responses may vary according to the selected model;
- the model may produce recipes requiring human validation;
- price and seasonal data may become outdated;
- the application does not replace nutritional or medical advice;
- local profile and conversation storage is not designed as a production multi-user database.

---

### 📄 License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE).

<p align="right"><a href="#top">⬆ Back to top</a></p>
