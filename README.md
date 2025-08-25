# 🗂️ Remote Workspace (Streamlit + Supabase)

Workspace collaboratif (calendrier, to‑do, notes, dépôt de fichiers) 100% gratuit à héberger, sans PC à laisser tourner.

## ✨ Fonctionnalités
- Authentification (email + mot de passe) via Supabase (gratuit).
- Espaces de travail (workspaces) avec invitations par email.
- 📅 Calendrier : créer / lister / supprimer des événements.
- ✅ To‑Do : tâches avec échéance et statut.
- 📝 Notes : créer, éditer, supprimer.
- 📁 Fichiers : upload / liste / suppression via Supabase Storage (bucket public).

## 🧰 Stack
- **UI** : Streamlit (hébergement gratuit via *Streamlit Community Cloud*).
- **Backend & DB** : Supabase (Postgres + Auth + Storage – offre gratuite).
- **Langage** : Python.

---

## 🚀 Déploiement en 15 minutes

### 1) Crée un projet Supabase (gratuit)
- Va sur supabase.com, crée un compte puis un **nouveau projet**.
- Récupère dans **Project Settings → API** : `Project URL` et `anon public key`.

### 2) Crée les tables & policies
- Dans **SQL Editor**, colle et exécute le contenu de `schema.sql` (inclus dans ce repo).
- Dans **Storage**, crée un bucket nommé `files` et rends‑le **public**.

### 3) Déploie l'app sur *Streamlit Community Cloud*
- Va sur `share.streamlit.io`, connecte ton repo GitHub (ou upload ce dossier).
- Dans *Advanced settings → Secrets*, ajoute :
  ```
  SUPABASE_URL = "https://..."
  SUPABASE_ANON_KEY = "ey..."
  ```
- Fichier principal : `app.py`.
- Laisse Streamlit installer `requirements.txt` automatiquement.

> Alternative : déployer sur Render / Railway (free).

---

## 🔒 Sécurité & droits
- Les **RLS Policies** (Row Level Security) incluses dans `schema.sql` font en sorte que chaque utilisateur ne voie que les données de ses workspaces (où il est membre ou invité).
- Les fichiers du bucket `files` sont publics par défaut pour simplifier le partage : change la policy si tu veux des URLs signées uniquement.

---

## 👥 Gérer les membres
- Dans la barre latérale, tu peux **créer un espace** et inviter des emails (séparés par des virgules).
- Les invités doivent **se créer un compte** avec le **même email** pour accéder à l'espace.

---

## 🧪 Lancement en local (optionnel)
```bash
pip install -r requirements.txt
export SUPABASE_URL="..."
export SUPABASE_ANON_KEY="..."
streamlit run app.py
```

---

## 🛠️ Personnalisation
- Tu peux ajouter des tags/priorités aux tâches, des rappels d'événements, des URL signées pour les fichiers, etc.
- Tout est en Python, simple à modifier.

Bon build ! 🚀