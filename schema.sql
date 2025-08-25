-- Enable UUID extension if needed
create extension if not exists "uuid-ossp";

-- Workspaces
create table if not exists public.workspaces (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  created_at timestamp with time zone default now()
);

-- Membership
create table if not exists public.workspace_members (
  workspace_id uuid references public.workspaces(id) on delete cascade,
  user_id uuid not null, -- supabase auth user id
  created_at timestamp with time zone default now(),
  primary key (workspace_id, user_id)
);

-- Invitations (by email)
create table if not exists public.workspace_invites (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  email text not null,
  created_at timestamp with time zone default now()
);

-- Events (Calendar)
create table if not exists public.events (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  title text not null,
  description text,
  start_ts timestamp with time zone not null,
  end_ts timestamp with time zone not null,
  created_at timestamp with time zone default now()
);

-- Todos
create table if not exists public.todos (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  title text not null,
  status text not null default 'open', -- open | done
  due_date date,
  created_at timestamp with time zone default now()
);

-- Notes
create table if not exists public.notes (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  title text not null,
  content text,
  updated_at timestamp with time zone default now()
);

-- Auto-update updated_at on notes
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_notes_updated on public.notes;
create trigger trg_notes_updated
before update on public.notes
for each row execute procedure public.set_updated_at();

-- Security: enable RLS
alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.workspace_invites enable row level security;
alter table public.events enable row level security;
alter table public.todos enable row level security;
alter table public.notes enable row level security;

-- Helper: check if current user is a member of a workspace or invited by email
create or replace function public.is_member(ws uuid) returns boolean language sql stable as $$
  select exists (
    select 1 from public.workspace_members m
    where m.workspace_id = ws and m.user_id = auth.uid()
  );
$$;

-- Policies
-- Workspaces: a user can select workspaces where he is a member; insert allowed by any authenticated user
create policy "workspaces_select_member"
on public.workspaces for select
using (public.is_member(id));

create policy "workspaces_insert_any_auth"
on public.workspaces for insert
to authenticated
with check (true);

-- Workspace members: only members of that workspace can select; insert allowed for any authenticated (to add themselves) 
create policy "members_select_member"
on public.workspace_members for select
using (public.is_member(workspace_id));

create policy "members_insert_self"
on public.workspace_members for insert
to authenticated
with check (auth.uid() = user_id);

-- Invites: members can manage invites
create policy "invites_select_member"
on public.workspace_invites for select
using (public.is_member(workspace_id));

create policy "invites_insert_member"
on public.workspace_invites for insert
to authenticated
with check (public.is_member(workspace_id));

create policy "invites_delete_member"
on public.workspace_invites for delete
using (public.is_member(workspace_id));

-- Events/Todos/Notes: accessible only if user is member
create policy "events_member"
on public.events for all
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));

create policy "todos_member"
on public.todos for all
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));

create policy "notes_member"
on public.notes for all
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));