# WhatsApp Sentiment Lab

Application d’analyse des sentiments à partir d’un export de conversation WhatsApp.

## Structure

```text
backend/   API FastAPI, entraînement NLP, modèle local et base SQLite
client/    Interface Next.js
```

Le système fonctionne uniquement avec un fichier de conversation exporté depuis
WhatsApp. Il accepte les formats `.txt` et `.zip`. Lorsqu’une archive ZIP contient des
médias, seuls les fichiers texte sont lus ; les médias ne sont pas traités.

## Prérequis

- Python 3.11 ou version ultérieure
- Node.js 20 ou version ultérieure
- npm
- Environ 8 Go d’espace libre pour PyTorch, Transformers et le modèle
- Git LFS pour récupérer l’artefact entraîné depuis GitHub

## 1. Préparer les données d’entraînement

Le projet utilise AfroXLMR-small comme encodeur multilingue adapté aux langues
africaines. Le classifieur de sentiment est entraîné localement sur des exemples
annotés par l’utilisateur. Aucun appel API n’est nécessaire.

Créez `backend/training_data.jsonl` en copiant `backend/training_data.example.jsonl` :

```bash
cp backend/training_data.example.jsonl backend/training_data.jsonl
```
Chaque ligne doit contenir un objet JSON avec un message et son sentiment :

```json
{"text":"Votre message ici","label":"positive"}
```

Les labels obligatoires sont `positive`, `neutral` et `negative`. Utilisez des
messages réellement représentatifs du groupe : français, swahili, swahili de
Bukavu, argot et messages avec code-switching entre ces langues. Les données sont
réparties en
trois ensembles (entraînement, validation, test) ; le script exige donc au minimum
trois exemples par label, mais plusieurs centaines d’exemples équilibrés sont
recommandés pour obtenir un modèle réellement exploitable.

Les principaux réglages du modèle sont dans `backend/settings.py` :

```python
HOST = "127.0.0.1"
PORT = 8000
LOCAL_MODEL_NAME = "Davlan/afro-xlmr-small"
TRAINING_DATA_PATH = BASE_DIR / "training_data.jsonl"
LOCAL_MODEL_PATH = BASE_DIR / "model_artifacts" / "afroxlmr_sentiment"
LOCAL_INFERENCE_BATCH_SIZE = 4
```

Par défaut, seul le classifieur final est entraîné et l’encodeur AfroXLMR-small reste
gelé. Cette configuration est recommandée pour un ordinateur sans GPU et avec 8 Go
de RAM.

## 2. Installer les dépendances et préparer le modèle

Depuis le dossier racine du projet :

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Sous Windows PowerShell :

```powershell
backend\.venv\Scripts\Activate.ps1
```

Les dépendances principales sont les suivantes. PyTorch est installé en version
CPU-only afin d’éviter les composants CUDA inutiles sur un ordinateur sans GPU :

- FastAPI pour l’API HTTP
- PyTorch pour l’entraînement et l’inférence CPU
- Transformers pour AfroXLMR-small
- `sentencepiece` et `protobuf` pour le tokenizer d’AfroXLMR-small
- Uvicorn pour démarrer le serveur
- `python-multipart` pour les fichiers envoyés par formulaire

L’entraînement est effectué une seule fois par le propriétaire du projet :

```bash
python backend/train_model.py
```

La première exécution télécharge le modèle de base, puis enregistre le classifieur
entraîné dans le dossier défini par `LOCAL_MODEL_PATH`. Le F1 macro de validation
est recalculé après chaque époque ; seule l'époque qui obtient le meilleur score
est sauvegardée sur disque, pas nécessairement la dernière. Cela évite qu'un
nombre d'époques trop généreux n'écrase un bon point de contrôle par un modèle en
surapprentissage (perte d'entraînement proche de zéro mais F1 de validation en
baisse). Les métriques de validation et de test (précision et F1 macro) du
meilleur point de contrôle, ainsi que le numéro de cette époque, sont écrites
dans `training_metadata.json`.

Les hyperparamètres principaux sont ajustables en ligne de commande :

```text
--epochs            nombre d’époques (par défaut 3)
--batch-size         taille de lot (par défaut 8)
--max-length         longueur maximale d’un message en tokens (par défaut 128)
--learning-rate      taux d’apprentissage (par défaut 1e-3 tête seule, 2e-5 avec --full-fine-tune)
--validation-ratio   part des données réservée à la validation (par défaut 0.15)
--test-ratio         part des données réservée au test (par défaut 0.15)
```

Après l’entraînement, versionnez le dossier du modèle avec Git LFS :

```bash
git lfs install
git add .gitattributes backend/model_artifacts
git commit -m "Ajouter le modèle de sentiment entraîné"
git push
```

Le fichier `backend/training_data.jsonl` reste ignoré et ne doit pas être publié,
car il contient les messages annotés utilisés pour l’entraînement.

Pour entraîner aussi l’encodeur complet, utilisez cette option seulement si le temps
et la mémoire sont suffisants :

```bash
python backend/train_model.py --full-fine-tune
```

Une fois le modèle entraîné récupéré ou publié, démarrez le backend :

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
4. Attendez la fin de la classification locale.
5. Consultez les résultats dans **Vue d’ensemble** ou **Messages**.

L’importateur prend en charge les messages multilignes et plusieurs formats de date
WhatsApp. Il n’y a pas de protection contre les doublons : réimporter le même fichier
insère à nouveau tous ses messages.

## 5. Fonctionnalités disponibles

- Importation de fichiers WhatsApp `.txt` et `.zip`
- Classification positive, neutre, négative ou inconnue
- Prise en charge des messages multilingues par AfroXLMR-small
- Indication émotionnelle et résumé court dérivés localement du sentiment
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

### Le modèle local n’est pas disponible

Installez Git LFS et exécutez `git lfs pull` après le clonage. Le backend doit
trouver l’artefact dans `backend/model_artifacts/afroxlmr_sentiment/`. Le réentraînement
n’est nécessaire que si l’artefact n’est pas publié.

### Le frontend ne trouve pas l’API

Vérifiez `NEXT_PUBLIC_API_BASE_URL` dans `client/.env.local`, puis redémarrez Next.js.

### Le fichier n’est pas accepté

Vérifiez qu’il s’agit d’un export WhatsApp `.txt` ou d’une archive `.zip` contenant un
fichier texte de conversation.
