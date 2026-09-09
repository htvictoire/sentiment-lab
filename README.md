# WhatsApp Sentiment Lab

Application d’analyse des sentiments à partir d’un export de conversation WhatsApp.

## Structure

```text
backend/   API FastAPI, traitement NLP, Gemini et base SQLite
client/    Interface Next.js
```

Le système fonctionne uniquement avec un fichier de conversation exporté depuis
WhatsApp. Il accepte les formats `.txt` et `.zip`. Lorsqu’une archive ZIP contient des
médias, seuls les fichiers texte sont lus ; les médias ne sont pas traités.

## Prérequis

- Python 3.11 ou version ultérieure
- Node.js 20 ou version ultérieure
- npm
- Une clé API Gemini

## 1. Configuration de Gemini

Obtenez une clé API depuis Google AI Studio, puis ouvrez le fichier :

```text
backend/settings.py
```

Remplacez la valeur vide de `GEMINI_API_KEY` :

```python
GEMINI_API_KEY = "VOTRE_CLE_API_GEMINI"
```

La clé doit être placée entre guillemets. Ne publiez jamais une vraie clé API dans un
dépôt public ou dans une capture d’écran.

Les autres réglages principaux se trouvent dans le même fichier :

```python
HOST = "127.0.0.1"
PORT = 8000
GEMINI_MODEL = "gemini-3.7-flash"
GEMINI_BATCH_SIZE = 25
```

`GEMINI_BATCH_SIZE` définit le nombre de messages envoyés dans une même requête
Gemini. Une valeur de 25 réduit le nombre d’appels tout en gardant des réponses
fiables. Diminuez-la si les messages sont très longs.

Pour tester l’interface sans appeler Gemini, définissez temporairement :

```python
DEMO_MODE = True
```

Les messages seront alors enregistrés sans classification réelle. Pour utiliser
Gemini, remettez `DEMO_MODE = False` et ajoutez une clé valide.

## 2. Installation et lancement du backend

Depuis le dossier racine du projet :

```bash
python3 -m venv backend/.venv
```

Activez l’environnement virtuel :

```bash
source backend/.venv/bin/activate
```

Sous Windows PowerShell :

```powershell
backend\.venv\Scripts\Activate.ps1
```

Installez les dépendances :

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Les dépendances installées sont :

- FastAPI pour l’API HTTP
- Uvicorn pour démarrer le serveur
- `python-multipart` pour les fichiers envoyés par formulaire
- `google-genai` pour l’appel à Gemini

Démarrez le backend :

```bash
python backend/app.py
```

La base SQLite est créée automatiquement au premier démarrage. Aucune migration ou
commande supplémentaire n’est nécessaire.

## 3. Installation et lancement du frontend

Dans un autre terminal, depuis le dossier racine :

```bash
cd client
npm install
cp .env.local.example .env.local
```

Ouvrez `client/.env.local` et configurez l’URL de l’API :

```env
NEXT_PUBLIC_API_BASE_URL=<URL_DE_L_API>/api
```

L’URL de l’API doit correspondre à l’adresse et au port définis dans
`backend/settings.py`.

Démarrez ensuite Next.js :

```bash
npm run dev
```

Ouvrez l’adresse indiquée par Next.js dans votre navigateur.

## 4. Importer une conversation

1. Ouvrez l’onglet **Accueil**.
2. Déposez un export WhatsApp `.txt` ou `.zip` dans la zone d’importation.
3. Cliquez sur **Importer et classer**.
4. Attendez la fin du traitement Gemini.
5. Consultez les résultats dans **Vue d’ensemble** ou **Messages**.

L’importateur prend en charge les messages multilignes et plusieurs formats de date
WhatsApp. Une même conversation importée deux fois n’est pas enregistrée en double.

## 5. Fonctionnalités disponibles

- Importation de fichiers WhatsApp `.txt` et `.zip`
- Détection de la langue et des messages multilingues
- Classification positive, neutre, négative ou inconnue
- Détection des émotions
- Résumé de chaque message
- Recherche de messages
- Filtre par sentiment
- Graphique de tendance des sentiments
- Graphique des émotions
- Détection des pics de sentiment négatif
- Sélection de périodes de 24 heures, 7, 30 ou 90 jours

## 6. API

Les routes principales sont :

```text
GET  /api/health/
GET  /api/messages/
POST /api/messages/import/
GET  /api/dashboard/summary/
```

La documentation interactive FastAPI est disponible sur :

```text
/docs
```

## Dépannage

### La clé Gemini n’est pas configurée

Vérifiez `GEMINI_API_KEY` dans `backend/settings.py`, puis redémarrez le backend.

### Le frontend ne trouve pas l’API

Vérifiez `NEXT_PUBLIC_API_BASE_URL` dans `client/.env.local`, puis redémarrez Next.js.

### Le fichier n’est pas accepté

Vérifiez qu’il s’agit d’un export WhatsApp `.txt` ou d’une archive `.zip` contenant un
fichier texte de conversation.
