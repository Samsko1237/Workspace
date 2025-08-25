
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client
from uuid import uuid4

def get_client(url: str, anon_key: str) -> Client:
    return create_client(url, anon_key)

# ---------------- Auth ----------------
def sign_up(sb: Client, email: str, password: str) -> Tuple[bool, str]:
    try:
        sb.auth.sign_up({"email": email, "password": password})
        # After sign_up, user must verify email; but for simplicity we try to sign in directly
        sb.auth.sign_in_with_password({"email": email, "password": password})
        return True, "ok"
    except Exception as e:
        return False, str(e)

def sign_in(sb: Client, email: str, password: str) -> Tuple[bool, str]:
    try:
        sb.auth.sign_in_with_password({"email": email, "password": password})
        return True, "ok"
    except Exception as e:
        return False, str(e)

def sign_out(sb: Client):
    try:
        sb.auth.sign_out()
    except Exception:
        pass

def get_user(sb: Optional[Client]) -> Optional[Dict[str, Any]]:
    if not sb:
        return None
    try:
        res = sb.auth.get_user()
        return res.user.__dict__ if res and res.user else None
    except Exception:
        return None

# ---------------- Workspaces ----------------
def list_workspaces_for_user(sb: Client) -> List[Dict[str, Any]]:
    user = get_user(sb)
    if not user:
        return []
    uid = user["id"]
    data = sb.table("workspace_members").select("workspaces(id,name)").eq("user_id", uid).execute()
    out = []
    for row in data.data:
        ws = row.get("workspaces")
        if ws:
            out.append(ws)
    return out

def ensure_workspace(sb: Client, name: str, invite_emails: List[str]) -> Dict[str, Any]:
    user = get_user(sb)
    uid = user["id"]
    # upsert workspace by name for this user, else create
    # create
    ws = sb.table("workspaces").insert({"name": name}).execute().data[0]
    # add current user as member
    sb.table("workspace_members").insert({"workspace_id": ws["id"], "user_id": uid}).execute()
    # record invitations (store emails; members must sign up with the same email)
    for em in invite_emails:
        sb.table("workspace_invites").insert({"workspace_id": ws["id"], "email": em}).execute()
    return ws

def switch_workspace(sb: Client, workspace_id: str) -> Dict[str, Any]:
    data = sb.table("workspaces").select("*").eq("id", workspace_id).single().execute()
    return data.data

# ---------------- Calendar ----------------
def create_event(sb: Client, workspace_id: str, title: str, description: str, start_ts: datetime, end_ts: datetime):
    sb.table("events").insert({
        "workspace_id": workspace_id,
        "title": title,
        "description": description,
        "start_ts": start_ts.isoformat(),
        "end_ts": end_ts.isoformat(),
    }).execute()

def list_events(sb: Client, workspace_id: str) -> List[Dict[str, Any]]:
    res = sb.table("events").select("*").eq("workspace_id", workspace_id).order("start_ts", desc=False).execute()
    return res.data

def delete_event(sb: Client, event_id: str):
    sb.table("events").delete().eq("id", event_id).execute()

# ---------------- ToDos ----------------
def create_todo(sb: Client, workspace_id: str, title: str, due_date: date):
    sb.table("todos").insert({
        "workspace_id": workspace_id,
        "title": title,
        "status": "open",
        "due_date": due_date.isoformat()
    }).execute()

def list_todos(sb: Client, workspace_id: str) -> List[Dict[str, Any]]:
    res = sb.table("todos").select("*").eq("workspace_id", workspace_id).order("due_date", desc=False).execute()
    return res.data

def update_todo_status(sb: Client, todo_id: str, status: str):
    sb.table("todos").update({"status": status}).eq("id", todo_id).execute()

def delete_todo(sb: Client, todo_id: str):
    sb.table("todos").delete().eq("id", todo_id).execute()

# ---------------- Notes ----------------
def create_note(sb: Client, workspace_id: str, title: str, content: str):
    sb.table("notes").insert({
        "workspace_id": workspace_id,
        "title": title,
        "content": content
    }).execute()

def list_notes(sb: Client, workspace_id: str) -> List[Dict[str, Any]]:
    res = sb.table("notes").select("*").eq("workspace_id", workspace_id).order("updated_at", desc=True).execute()
    return res.data

def update_note(sb: Client, note_id: str, content: str):
    sb.table("notes").update({"content": content}).eq("id", note_id).execute()

def delete_note(sb: Client, note_id: str):
    sb.table("notes").delete().eq("id", note_id).execute()

# ---------------- Files (Supabase Storage) ----------------
def upload_file(sb: Client, workspace_id: str, file):
    try:
        bucket = "files"
        filename = f"{workspace_id}/{uuid4()}_{file.name}"
        sb.storage.from_(bucket).upload(filename, file.getbuffer())
        # make public URL (assumes bucket is public)
        public_url = sb.storage.from_(bucket).get_public_url(filename)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def list_files(sb: Client, workspace_id: str) -> List[Dict[str, Any]]:
    try:
        bucket = "files"
        listing = sb.storage.from_(bucket).list(workspace_id)
        out = []
        for item in listing:
            path = f"{workspace_id}/{item['name']}"
            url = sb.storage.from_(bucket).get_public_url(path)
            out.append({
                "id": item["id"] if "id" in item else item["name"],
                "name": path,
                "public_url": url,
                "metadata": {"size": item.get("size", None)}
            })
        return out
    except Exception:
        return []

def delete_file(sb: Client, path: str):
    bucket = "files"
    sb.storage.from_(bucket).remove([path])
