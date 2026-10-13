-- Run as the project administrator after creating a dedicated LOGIN role
-- named mini_monitor_app with a privately generated password.
GRANT CONNECT ON DATABASE postgres TO mini_monitor_app;
GRANT USAGE ON SCHEMA public TO mini_monitor_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users, public.http_events, public.notes TO mini_monitor_app;
GRANT USAGE, SELECT ON SEQUENCE public.users_id_seq, public.http_events_id_seq, public.notes_id_seq TO mini_monitor_app;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.http_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;
CREATE POLICY mini_monitor_server_users ON public.users FOR ALL TO mini_monitor_app USING (true) WITH CHECK (true);
CREATE POLICY mini_monitor_server_events ON public.http_events FOR ALL TO mini_monitor_app USING (true) WITH CHECK (true);
CREATE POLICY mini_monitor_server_notes ON public.notes FOR ALL TO mini_monitor_app USING (true) WITH CHECK (true);
