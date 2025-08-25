
import os
import time
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import streamlit as st

from supabase_helpers import (
    get_client,
    sign_up,
    sign_in,
    sign_out,
    get_user,
    ensure_workspace,
    list_workspaces_for_user,
    switch_workspace,
    create_event, list_events, delete_event,
    create_todo, list_todos, update_todo_status, delete_todo,
    create_note, list_notes, update_note, delete_note,
    upload_file, list_files, delete_file,
)

st.set_page_config(page_title="Remote Workspace", page_icon="🗂️", layout="wide")

# ---------------------- Helpers ----------------------
def require_auth():
    user = get_user(st.session_state.get("sb"))
    if not user:
        st.info("Connectez-vous ou créez un compte pour continuer.")
        return False
    return True

def init_state():
    for k, v in {
        "sb": None,
        "workspace": None,
        "workspace_list": [],
        "auth_mode": "login",
    }.items():
        st.session_state.setdefault(k, v)

init_state()

# ---------------------- Sidebar: Auth ----------------------
st.sidebar.title("🔐 Authentification")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.sidebar.error("Configurez SUPABASE_URL et SUPABASE_ANON_KEY (Secrets Streamlit).")
else:
    if not st.session_state["sb"]:
        st.session_state["sb"] = get_client(SUPABASE_URL, SUPABASE_ANON_KEY)

user = get_user(st.session_state["sb"]) if st.session_state["sb"] else None

if not user:
    st.sidebar.toggle("Créer un compte (sinon connexion)", key="toggle_signup")
    st.session_state["auth_mode"] = "signup" if st.session_state["toggle_signup"] else "login"

    with st.sidebar.form("auth_form"):
        st.write("Mode:", "Création" if st.session_state["auth_mode"] == "signup" else "Connexion")
        email = st.text_input("Email")
        pwd = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Valider")
        if submitted and email and pwd and st.session_state["sb"]:
            try:
                if st.session_state["auth_mode"] == "signup":
                    ok, msg = sign_up(st.session_state["sb"], email, pwd)
                else:
                    ok, msg = sign_in(st.session_state["sb"], email, pwd)
                if ok:
                    st.experimental_rerun()
                else:
                    st.sidebar.error(msg)
            except Exception as e:
                st.sidebar.error(f"Erreur: {e}")
else:
    st.sidebar.success(f"Connecté: {user.get('email')}")
    if st.sidebar.button("Se déconnecter"):
        sign_out(st.session_state["sb"])
        st.experimental_rerun()

# ---------------------- Sidebar: Workspace ----------------------
if user:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧩 Espace de travail")
    # Load workspaces
    st.session_state["workspace_list"] = list_workspaces_for_user(st.session_state["sb"])

    if st.session_state["workspace_list"]:
        names = [w["name"] for w in st.session_state["workspace_list"]]
        idx = 0
        # Determine current workspace
        if st.session_state["workspace"]:
            for i, w in enumerate(st.session_state["workspace_list"]):
                if w["id"] == st.session_state["workspace"]["id"]:
                    idx = i
                    break
        choice = st.sidebar.selectbox("Choisir un espace", names, index=idx)
        chosen = st.session_state["workspace_list"][names.index(choice)]
        if not st.session_state["workspace"] or st.session_state["workspace"]["id"] != chosen["id"]:
            st.session_state["workspace"] = chosen
    else:
        st.sidebar.info("Aucun espace encore. Créez-en un ci-dessous.")

    with st.sidebar.form("create_ws"):
        ws_name = st.text_input("Nom de l'espace")
        members = st.text_area("Inviter par email (séparés par des virgules)", help="Les invités devront créer un compte avec le même email.")
        if st.form_submit_button("Créer / Mettre à jour"):
            try:
                w = ensure_workspace(st.session_state["sb"], ws_name.strip(), invite_emails=[m.strip() for m in members.split(",") if m.strip()])
                st.session_state["workspace"] = w
                st.success("Espace créé/mis à jour.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")

# ---------------------- Main UI ----------------------
st.title("🗂️ Remote Workspace")
st.caption("Calendrier • To‑Do • Notes • Fichiers (multi‑utilisateurs)")

if not require_auth():
    st.stop()

if not st.session_state["workspace"]:
    st.warning("Créez ou choisissez un espace de travail dans la barre latérale.")
    st.stop()

tabs = st.tabs(["📅 Calendrier", "✅ To‑Do", "📝 Notes", "📁 Fichiers"])

# ---------------------- Calendar Tab ----------------------
with tabs[0]:
    st.subheader("📅 Calendrier")
    with st.form("add_event"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Titre de l'événement")
            start = st.date_input("Début", value=date.today())
        with col2:
            desc = st.text_area("Description", height=80)
            end = st.date_input("Fin", value=date.today())
        submitted = st.form_submit_button("Ajouter")
        if submitted and title:
            create_event(st.session_state["sb"], st.session_state["workspace"]["id"], title, desc, datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time()))
            st.success("Événement ajouté.")
            time.sleep(0.4)
            st.experimental_rerun()

    st.markdown("### Événements à venir")
    events = list_events(st.session_state["sb"], st.session_state["workspace"]["id"])
    if not events:
        st.info("Aucun événement.")
    else:
        for ev in events:
            with st.expander(f"{ev['title']} — {ev['start_ts'][:10]} → {ev['end_ts'][:10]}"):
                st.write(ev.get("description") or "")
                c1, c2 = st.columns(2)
                with c1:
                    st.caption(f"Début: {ev['start_ts']}")
                with c2:
                    st.caption(f"Fin: {ev['end_ts']}")
                if st.button("Supprimer", key=f"del_ev_{ev['id']}"):
                    delete_event(st.session_state["sb"], ev["id"])
                    st.experimental_rerun()

# ---------------------- To-Do Tab ----------------------
with tabs[1]:
    st.subheader("✅ To‑Do")
    with st.form("add_todo"):
        col1, col2 = st.columns([3,1])
        with col1:
            ttext = st.text_input("Tâche")
        with col2:
            due = st.date_input("Échéance", value=date.today())
        submitted = st.form_submit_button("Ajouter")
        if submitted and ttext:
            create_todo(st.session_state["sb"], st.session_state["workspace"]["id"], ttext, due)
            st.success("Tâche ajoutée.")
            time.sleep(0.3)
            st.experimental_rerun()

    todos = list_todos(st.session_state["sb"], st.session_state["workspace"]["id"])
    if not todos:
        st.info("Aucune tâche.")
    else:
        for td in todos:
            cols = st.columns([0.7, 0.15, 0.15])
            with cols[0]:
                st.write(f"**{td['title']}** — due {td['due_date']}")
                if td["status"] == "done":
                    st.caption("✅ Terminée")
                else:
                    st.caption("⏳ En cours")
            with cols[1]:
                if td["status"] != "done":
                    if st.button("Marquer terminé", key=f"done_{td['id']}"):
                        update_todo_status(st.session_state["sb"], td["id"], "done")
                        st.experimental_rerun()
            with cols[2]:
                if st.button("Supprimer", key=f"del_td_{td['id']}"):
                    delete_todo(st.session_state["sb"], td["id"])
                    st.experimental_rerun()

# ---------------------- Notes Tab ----------------------
with tabs[2]:
    st.subheader("📝 Notes")
    with st.form("add_note"):
        title = st.text_input("Titre")
        content = st.text_area("Contenu", height=150)
        if st.form_submit_button("Créer"):
            if title.strip():
                create_note(st.session_state["sb"], st.session_state["workspace"]["id"], title, content)
                st.success("Note créée.")
                time.sleep(0.3)
                st.experimental_rerun()

    notes = list_notes(st.session_state["sb"], st.session_state["workspace"]["id"])
    if not notes:
        st.info("Aucune note.")
    else:
        for nt in notes:
            with st.expander(f"📝 {nt['title']} (modifié {nt['updated_at']})"):
                new_content = st.text_area("Modifier", value=nt.get("content") or "", key=f"edit_{nt['id']}", height=200)
                cols = st.columns(2)
                with cols[0]:
                    if st.button("Enregistrer", key=f"save_{nt['id']}"):
                        update_note(st.session_state["sb"], nt["id"], new_content)
                        st.success("Enregistré.")
                        time.sleep(0.2)
                        st.experimental_rerun()
                with cols[1]:
                    if st.button("Supprimer", key=f"del_note_{nt['id']}"):
                        delete_note(st.session_state["sb"], nt["id"])
                        st.experimental_rerun()

# ---------------------- Files Tab ----------------------
with tabs[3]:
    st.subheader("📁 Dépôt de fichiers (Stockage Supabase)")
    up = st.file_uploader("Uploader un fichier", key="uploader")
    if up is not None:
        ok, msg = upload_file(st.session_state["sb"], st.session_state["workspace"]["id"], up)
        if ok:
            st.success("Fichier uploadé.")
            time.sleep(0.3)
            st.experimental_rerun()
        else:
            st.error(msg)

    files = list_files(st.session_state["sb"], st.session_state["workspace"]["id"])
    if not files:
        st.info("Aucun fichier dans ce workspace.")
    else:
        for f in files:
            cols = st.columns([0.5, 0.3, 0.2])
            with cols[0]:
                st.write(f"**{f['name'].split('/')[-1]}**")
                st.caption(f"Taille: {f.get('metadata', {}).get('size', 'n/a')}")
            with cols[1]:
                public_url = f.get('public_url')
                if public_url:
                    st.markdown(f"[Télécharger]({public_url})")
            with cols[2]:
                if st.button("Supprimer", key=f"del_file_{f['id']}"):
                    delete_file(st.session_state["sb"], f["name"])
                    st.experimental_rerun()
