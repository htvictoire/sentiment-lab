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

Le modèle de classification est déjà entraîné et inclus dans le dépôt (dossier
`backend/model_artifacts/`, récupéré via Git LFS). Il n’est pas nécessaire de
l’entraîner à nouveau pour utiliser l’application ; cette étape reste possible et est
décrite plus bas, pour qui veut le réentraîner sur d’autres données.

## Prérequis

- Windows 10 ou 11 (ce guide suit ce système ; les commandes équivalentes pour
  macOS/Linux sont données entre parenthèses)
- Environ 8 Go d’espace disque libre (Python, Node.js, PyTorch et le modèle)
- Une connexion internet pour télécharger les outils, le dépôt et le modèle

Aucune expérience préalable de Git, Python ou Node.js n’est nécessaire : chaque
étape ci-dessous est décrite en détail.

## Guide d’installation détaillé (Windows)

### Étape 1 : Installer Git et Git LFS

Git sert à télécharger (« cloner ») le code du projet. Git LFS est une extension de
Git nécessaire pour télécharger le modèle entraîné, qui est un fichier volumineux
(environ 540 Mo).

1. Ouvrez [git-scm.com/download/win](https://git-scm.com/download/win) et
   téléchargez l’installeur (le téléchargement démarre automatiquement).
2. Lancez le fichier téléchargé. Sur l’écran **Select Components**, cochez la case
   **Git LFS (Large File Support)** si elle est présente, puis laissez toutes les
   autres options par défaut et cliquez sur **Next** jusqu’à **Install**.
3. Une fois l’installation terminée, ouvrez le menu Démarrer, tapez `Git Bash` et
   lancez cette application. Toutes les commandes de ce guide s’exécutent dans
   cette fenêtre, sauf indication contraire.
4. Dans Git Bash, vérifiez que Git fonctionne :

   ```bash
   git --version
   ```

5. Si l’étape 2 n’a pas installé Git LFS (la commande suivante affiche une erreur),
   téléchargez-le séparément sur [git-lfs.com](https://git-lfs.com), installez-le,
   puis relancez Git Bash. Initialisez ensuite Git LFS une seule fois sur votre
   ordinateur :

   ```bash
   git lfs install
   ```

   Cette commande doit afficher `Git LFS initialized.`.

### Étape 2 : Cloner le dépôt

Toujours dans Git Bash, placez-vous dans le dossier où vous voulez installer le
projet (par exemple vos Documents), puis clonez le dépôt :

```bash
cd ~/Documents
git clone https://github.com/htvictoire/sentiment-lab.git
cd sentiment-lab
```

Comme Git LFS a été initialisé avant le clonage, le modèle entraîné est récupéré
automatiquement pendant cette étape. Si vous avez un doute, exécutez tout de suite
après :

```bash
git lfs pull
```

Vérifiez que le modèle a bien été téléchargé en entier (pas seulement un pointeur
de quelques octets) :

```bash
ls -lh backend/model_artifacts/afroxlmr_sentiment/model.safetensors
```

La taille affichée doit être d’environ 540 Mo. Si elle affiche seulement quelques
centaines d’octets, Git LFS n’a pas fonctionné : reprenez l’étape 1, puis relancez
`git lfs pull` depuis le dossier `sentiment-lab`.

### Étape 3 : Installer Python

1. Ouvrez [python.org/downloads](https://www.python.org/downloads/) et téléchargez
   la dernière version 3.11 ou ultérieure.
2. Lancez l’installeur. **Cochez impérativement la case « Add python.exe to PATH »**
   en bas de la première fenêtre avant de cliquer sur **Install Now**. C’est
   l’erreur la plus fréquente : sans cette case, Python ne sera pas reconnu dans le
   terminal.
3. Fermez puis rouvrez Git Bash (obligatoire pour que le PATH soit pris en compte),
   puis vérifiez :

   ```bash
   python --version
   ```

   Si cette commande ne fonctionne pas mais que `py --version` fonctionne, utilisez
   `py` à la place de `python` dans toutes les commandes qui suivent.

### Étape 4 : Installer les dépendances du backend

Depuis le dossier `sentiment-lab` (racine du projet), créez un environnement
virtuel Python, c’est-à-dire un espace isolé pour les bibliothèques du projet :

```bash
python -m venv backend/.venv
```

Activez cet environnement. La commande dépend du terminal utilisé :

```bash
# Git Bash (recommandé, utilisé dans le reste de ce guide)
source backend/.venv/Scripts/activate
```

```powershell
# PowerShell
backend\.venv\Scripts\Activate.ps1
```

Si PowerShell affiche une erreur du type « l’exécution de scripts est
désactivée sur ce système », exécutez une seule fois cette commande dans
PowerShell, puis réessayez :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

```cmd
:: Invite de commandes (cmd.exe)
backend\.venv\Scripts\activate.bat
```

Une fois l’environnement activé, son nom (`.venv`) apparaît au début de la ligne de
commande. Installez ensuite les dépendances (cette étape télécharge PyTorch et peut
prendre plusieurs minutes) :

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Les dépendances installées sont :

- FastAPI pour l’API HTTP
- PyTorch (version CPU uniquement, sans composants GPU inutiles) pour l’inférence
- Transformers pour charger AfroXLMR-small
- `sentencepiece` et `protobuf` pour le tokenizer d’AfroXLMR-small
- Uvicorn pour démarrer le serveur
- `python-multipart` pour les fichiers envoyés par formulaire

### Étape 5 : Démarrer le backend

Toujours dans le même terminal, avec l’environnement virtuel activé et depuis la
racine du projet :

```bash
python backend/app.py
```

Le message `Uvicorn running on http://127.0.0.1:8000` doit s’afficher. Laissez cette
fenêtre ouverte : c’est le serveur qui classe les messages. La base de données
SQLite est créée automatiquement au premier démarrage.

### Étape 6 : Installer Node.js

1. Ouvrez [nodejs.org](https://nodejs.org) et téléchargez la version **LTS**
   (recommandée pour la plupart des utilisateurs).
2. Lancez l’installeur en laissant toutes les options par défaut.
3. Ouvrez une **nouvelle** fenêtre Git Bash (pas celle qui fait tourner le backend)
   et vérifiez :

   ```bash
   node --version
   npm --version
   ```

### Étape 7 : Installer et configurer le frontend

Dans cette nouvelle fenêtre Git Bash, placez-vous à la racine du projet puis dans
le dossier `client` :

```bash
cd ~/Documents/sentiment-lab
cd client
npm install
```

Cette commande peut prendre quelques minutes. Copiez ensuite le fichier de
configuration d’exemple :

```bash
cp .env.local.example .env.local
```

Le fichier `client/.env.local` contient déjà l’adresse par défaut du backend
(`http://127.0.0.1:8000/api`) : aucune modification n’est nécessaire si vous suivez
ce guide sans changer le port du backend.

### Étape 8 : Démarrer le frontend

Toujours dans le dossier `client` :

```bash
npm run dev
```

Une adresse s’affiche, généralement `http://localhost:3000`. Ouvrez-la dans votre
navigateur.

### Étape 9 : Utiliser l’application

1. Ouvrez l’onglet **Accueil**.
2. Déposez un export WhatsApp `.txt` ou `.zip` dans la zone d’importation.
3. Cliquez sur **Importer et classer**.
4. Attendez la fin de la classification locale (une page de chargement s’affiche
   pendant ce temps).
5. Consultez les résultats dans **Vue d’ensemble** ou **Messages**.

Les deux fenêtres ouvertes aux étapes 5 et 8 (backend et frontend) doivent rester
actives pendant toute l’utilisation de l’application.

## Réentraîner le modèle (optionnel)

Cette section ne concerne que celles et ceux qui veulent réentraîner le classifieur
sur d’autres données. Elle n’est pas nécessaire pour utiliser l’application, le
modèle fourni dans le dépôt étant déjà entraîné.

Le projet utilise AfroXLMR-small comme encodeur multilingue adapté aux langues
africaines. Le classifieur de sentiment est entraîné localement sur des exemples
annotés par l’utilisateur. Aucun appel API externe n’est nécessaire.

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
réparties en trois ensembles (entraînement, validation, test) ; le script exige
donc au minimum trois exemples par label, mais plusieurs centaines d’exemples
équilibrés sont recommandés pour obtenir un modèle réellement exploitable.

Les principaux réglages du modèle sont dans `backend/settings.py` :

```python
HOST = "127.0.0.1"
PORT = 8000
LOCAL_MODEL_NAME = "Davlan/afro-xlmr-small"
TRAINING_DATA_PATH = BASE_DIR / "training_data.jsonl"
LOCAL_MODEL_PATH = BASE_DIR / "model_artifacts" / "afroxlmr_sentiment"
LOCAL_INFERENCE_BATCH_SIZE = 4
```

Lancez l’entraînement (l’environnement virtuel doit être activé, voir étape 4
ci-dessus) :

```bash
python backend/train_model.py
```

La première exécution télécharge le modèle de base, puis enregistre le classifieur
entraîné dans le dossier défini par `LOCAL_MODEL_PATH`. Le F1 macro de validation
est recalculé après chaque époque ; seule l’époque qui obtient le meilleur score
est sauvegardée sur disque, pas nécessairement la dernière. Cela évite qu’un
nombre d’époques trop généreux n’écrase un bon point de contrôle par un modèle en
surapprentissage (perte d’entraînement proche de zéro mais F1 de validation en
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

Par défaut, seul le classifieur final est entraîné et l’encodeur AfroXLMR-small
reste gelé. Pour entraîner aussi l’encodeur complet (plus lent, demande plus de
mémoire, mais généralement plus précis) :

```bash
python backend/train_model.py --full-fine-tune
```

Après l’entraînement, versionnez le nouveau modèle avec Git LFS :

```bash
git lfs install
git add backend/model_artifacts
git commit -m "Mettre à jour le modèle de sentiment entraîné"
git push
```

Le fichier `backend/training_data.jsonl` reste ignoré par Git et ne doit pas être
publié, car il contient les messages annotés utilisés pour l’entraînement.

## Fonctionnalités disponibles

- Importation de fichiers WhatsApp `.txt` et `.zip`
- Classification positive, neutre, négative ou inconnue
- Prise en charge des messages multilingues par AfroXLMR-small
- Indication émotionnelle et résumé court dérivés localement du sentiment
- Recherche de messages et filtre par sentiment
- Suppression complète des messages stockés, avec confirmation
- Graphique de tendance des sentiments et graphique des émotions
- Détection des pics de sentiment négatif
- Filtre par période prédéfinie (24 heures, 7, 30, 90 jours) ou par plage de dates
  personnalisée

## API

Les routes principales sont :

```text
GET    /api/health/
GET    /api/messages/
DELETE /api/messages/
POST   /api/messages/import/
GET    /api/dashboard/summary/
```

La documentation interactive FastAPI est disponible sur :

```text
/docs
```

## Dépannage

### « python » ou « git » n’est pas reconnu comme commande

Le PATH n’a pas été mis à jour. Fermez complètement toutes les fenêtres de
terminal ouvertes et rouvrez Git Bash après l’installation de Python ou de Git.

### PowerShell refuse d’activer l’environnement virtuel

Exécutez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` dans PowerShell,
puis réessayez. Vous pouvez aussi utiliser Git Bash à la place de PowerShell pour
toutes les commandes de ce guide.

### Le modèle local n’est pas disponible

Vérifiez que Git LFS est installé (`git lfs version`), puis exécutez
`git lfs pull` depuis la racine du projet. Contrôlez ensuite que
`backend/model_artifacts/afroxlmr_sentiment/model.safetensors` fait bien environ
540 Mo (voir étape 2). Le réentraînement n’est nécessaire que si vous voulez
obtenir un modèle différent de celui fourni.

### Erreur « DLL initialization routine failed » lors du chargement de PyTorch

Si le démarrage du backend échoue avec une erreur `OSError: [WinError 1114]`
mentionnant `c10.dll` ou une autre bibliothèque du dossier `torch\lib`, il manque
généralement le **Microsoft Visual C++ Redistributable**, requis par PyTorch sur
Windows :

1. Téléchargez et installez
   [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe).
2. Redémarrez l’ordinateur, puis relancez `python backend/app.py`.

Si l’erreur persiste et que le projet se trouve dans un dossier synchronisé par
OneDrive (par exemple le Bureau), OneDrive peut ne pas avoir entièrement
téléchargé les fichiers de l’environnement virtuel sur l’ordinateur. Dans
l’explorateur de fichiers, faites un clic droit sur le dossier du projet et
choisissez **Toujours conserver sur cet appareil**, attendez la fin de la
synchronisation, puis réessayez. Il est aussi possible de déplacer le projet en
dehors d’un dossier synchronisé par OneDrive.

### Le frontend ne trouve pas l’API

Vérifiez `NEXT_PUBLIC_API_BASE_URL` dans `client/.env.local`, puis redémarrez
Next.js. Vérifiez aussi que la fenêtre du backend (étape 5) est toujours ouverte
et n’affiche pas d’erreur.

### Le fichier n’est pas accepté

Vérifiez qu’il s’agit d’un export WhatsApp `.txt` ou d’une archive `.zip`
contenant un fichier texte de conversation.
