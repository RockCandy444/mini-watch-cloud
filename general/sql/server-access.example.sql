-- Run as the project administrator after creating a dedicated LOGIN role
-- named mini_general_app with a privately generated password. No passwords
-- belong in this file. Do not grant access to the project's pre-existing notes.
GRANT CONNECT ON DATABASE postgres TO mini_general_app;
GRANT USAGE ON SCHEMA public TO mini_general_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users, public.posts TO mini_general_app;
GRANT USAGE, SELECT ON SEQUENCE public.users_id_seq, public.posts_id_seq TO mini_general_app;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY mini_general_server_users ON public.users FOR ALL TO mini_general_app USING (true) WITH CHECK (true);
CREATE POLICY mini_general_server_posts ON public.posts FOR ALL TO mini_general_app USING (true) WITH CHECK (true);
