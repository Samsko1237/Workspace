-- Enable UUID extension if needed
create extension if not exists "uuid-ossp";

-- ===============================
-- Tables
-- ===============================

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
  status text not null default 'open',
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

-- ===============================
-- Enable RLS
-- ===============================
alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.workspace_invites enable row level security;
alter table public.events enable row level security;
alter table public.todos enable row level security;
alter table public.notes enable row level security;

-- ===============================
-- Helper function
-- ===============================
create or replace function public.is_member(ws uuid) returns boolean language sql stable as $$
  select exists (
    select 1 from public.workspace_members m
    where m.workspace_id = ws and m.user_id = auth.uid()
  );
$$;

-- ===============================
-- Workspaces Policies
-- ===============================
drop policy if exists workspaces_select on public.workspaces;
create policy workspaces_select
on public.workspaces
for select
to authenticated
using (public.is_member(id));

drop policy if exists workspaces_insert on public.workspaces;
create policy workspaces_insert
on public.workspaces
for insert
to authenticated
with check (true);

drop policy if exists workspaces_update on public.workspaces;
create policy workspaces_update
on public.workspaces
for update
to authenticated
using (public.is_member(id));

drop policy if exists workspaces_delete on public.workspaces;
create policy workspaces_delete
on public.workspaces
for delete
to authenticated
using (public.is_member(id));

-- ===============================
-- Workspace Members Policies
-- ===============================
drop policy if exists members_select on public.workspace_members;
create policy members_select
on public.workspace_members
for select
using (public.is_member(workspace_id));

drop policy if exists members_insert on public.workspace_members;
create policy members_insert
on public.workspace_members
for insert
to authenticated
with check (
    auth.uid() = user_id -- l’utilisateur peut s’ajouter lui-même
    OR
    auth.uid() IN (select user_id from public.workspace_members where workspace_id = workspace_members.workspace_id) -- un membre existant peut ajouter
);

drop policy if exists members_update on public.workspace_members;
create policy members_update
on public.workspace_members
for update
using (public.is_member(workspace_id));

drop policy if exists members_delete on public.workspace_members;
create policy members_delete
on public.workspace_members
for delete
using (public.is_member(workspace_id));

-- ===============================
-- Workspace Invites Policies
-- ===============================
drop policy if exists invites_select on public.workspace_invites;
create policy invites_select
on public.workspace_invites
for select
using (public.is_member(workspace_id));

drop policy if exists invites_insert on public.workspace_invites;
create policy invites_insert
on public.workspace_invites
for insert
to authenticated
with check (public.is_member(workspace_id));

drop policy if exists invites_delete on public.workspace_invites;
create policy invites_delete
on public.workspace_invites
for delete
using (public.is_member(workspace_id));

-- ===============================
-- Events Policies
-- ===============================
drop policy if exists events_select on public.events;
create policy events_select
on public.events
for select
using (public.is_member(workspace_id));

drop policy if exists events_insert on public.events;
create policy events_insert
on public.events
for insert
to authenticated
with check (public.is_member(workspace_id));

drop policy if exists events_update on public.events;
create policy events_update
on public.events
for update
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));

drop policy if exists events_delete on public.events;
create policy events_delete
on public.events
for delete
using (public.is_member(workspace_id));

-- ===============================
-- Todos Policies
-- ===============================
drop policy if exists todos_select on public.todos;
create policy todos_select
on public.todos
for select
using (public.is_member(workspace_id));

drop policy if exists todos_insert on public.todos;
create policy todos_insert
on public.todos
for insert
to authenticated
with check (public.is_member(workspace_id));

drop policy if exists todos_update on public.todos;
create policy todos_update
on public.todos
for update
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));

drop policy if exists todos_delete on public.todos;
create policy todos_delete
on public.todos
for delete
using (public.is_member(workspace_id));

-- ===============================
-- Notes Policies
-- ===============================
drop policy if exists notes_select on public.notes;
create policy notes_select
on public.notes
for select
using (public.is_member(workspace_id));

drop policy if exists notes_insert on public.notes;
create policy notes_insert
on public.notes
for insert
to authenticated
with check (public.is_member(workspace_id));

drop policy if exists notes_update on public.notes;
create policy notes_update
on public.notes
for update
using (public.is_member(workspace_id))
with check (public.is_member(workspace_id));

drop policy if exists notes_delete on public.notes;
create policy notes_delete
on public.notes
for delete
using (public.is_member(workspace_id));
