


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE SCHEMA IF NOT EXISTS "public";


ALTER SCHEMA "public" OWNER TO "pg_database_owner";


COMMENT ON SCHEMA "public" IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."actions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tenant_id" "uuid",
    "type" "text" NOT NULL,
    "payload_json" "jsonb" NOT NULL,
    "status" "text" DEFAULT 'planned'::"text",
    "request_id" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."actions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."approvals" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "kind" "text",
    "source" "text",
    "title" "text",
    "summary" "text",
    "payload" "jsonb",
    "risk" "text",
    "status" "text",
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."approvals" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."audit_log" (
    "request_id" "text" NOT NULL,
    "tenant_id" "uuid",
    "dry_run" boolean DEFAULT true,
    "actions" "jsonb" NOT NULL,
    "results" "jsonb" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."audit_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."automations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "trigger" "jsonb",
    "conditions" "jsonb",
    "action" "jsonb",
    "enabled" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."automations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."client_sessions" (
    "token" "text" NOT NULL,
    "user_id" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "expires_at" timestamp with time zone
);


ALTER TABLE "public"."client_sessions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."connections" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tenant_id" "uuid",
    "provider" "text" NOT NULL,
    "access_token_encrypted" "text" NOT NULL,
    "refresh_token_encrypted" "text",
    "meta" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."connections" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."core_memory" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "level" "text",
    "key" "text",
    "value" "jsonb",
    "vector" "extensions"."vector"(1536),
    "meta" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "last_used_at" timestamp with time zone
);


ALTER TABLE "public"."core_memory" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."dedupe_keys" (
    "tenant_id" "uuid" NOT NULL,
    "external_id" "text" NOT NULL,
    "kind" "text" NOT NULL,
    "action_id" "uuid"
);


ALTER TABLE "public"."dedupe_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."drafts" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "recipients" "jsonb",
    "subject" "text",
    "body" "text",
    "tone" "text",
    "status" "text",
    "risk" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."drafts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."oauth_tokens" (
    "user_id" "text" NOT NULL,
    "provider" "text" NOT NULL,
    "access_token" "text" NOT NULL,
    "refresh_token" "text" NOT NULL,
    "expiry" timestamp with time zone NOT NULL,
    "scopes" "text"[] NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."oauth_tokens" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "whatsapp_user_id" "text",
    "google_user_id" "text",
    "locale" "text",
    "tz" "text"
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."rules" (
    "tenant_id" "uuid" NOT NULL,
    "yaml" "text" NOT NULL,
    "version" integer DEFAULT 1,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."rules" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tenant_settings" (
    "tenant_id" "uuid" NOT NULL,
    "key" "text" NOT NULL,
    "value" "text" NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."tenant_settings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tenants" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL
);


ALTER TABLE "public"."tenants" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tenant_id" "uuid",
    "email" "text" NOT NULL,
    "name" "text",
    "password_hash" "text" NOT NULL,
    "must_change_password" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."users" OWNER TO "postgres";


ALTER TABLE ONLY "public"."actions"
    ADD CONSTRAINT "actions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."approvals"
    ADD CONSTRAINT "approvals_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_log"
    ADD CONSTRAINT "audit_log_pkey" PRIMARY KEY ("request_id");



ALTER TABLE ONLY "public"."automations"
    ADD CONSTRAINT "automations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."client_sessions"
    ADD CONSTRAINT "client_sessions_pkey" PRIMARY KEY ("token");



ALTER TABLE ONLY "public"."connections"
    ADD CONSTRAINT "connections_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."core_memory"
    ADD CONSTRAINT "core_memory_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."dedupe_keys"
    ADD CONSTRAINT "dedupe_keys_pkey" PRIMARY KEY ("tenant_id", "external_id", "kind");



ALTER TABLE ONLY "public"."drafts"
    ADD CONSTRAINT "drafts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."oauth_tokens"
    ADD CONSTRAINT "oauth_tokens_pkey" PRIMARY KEY ("user_id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_google_user_id_key" UNIQUE ("google_user_id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_whatsapp_user_id_key" UNIQUE ("whatsapp_user_id");



ALTER TABLE ONLY "public"."rules"
    ADD CONSTRAINT "rules_pkey" PRIMARY KEY ("tenant_id");



ALTER TABLE ONLY "public"."tenant_settings"
    ADD CONSTRAINT "tenant_settings_pkey" PRIMARY KEY ("tenant_id", "key");



ALTER TABLE ONLY "public"."tenants"
    ADD CONSTRAINT "tenants_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_approvals_status_expires" ON "public"."approvals" USING "btree" ("status", "expires_at");



CREATE INDEX "idx_automations_enabled" ON "public"."automations" USING "btree" ("enabled");



CREATE INDEX "idx_core_memory_vector" ON "public"."core_memory" USING "ivfflat" ("vector");



CREATE INDEX "idx_drafts_status" ON "public"."drafts" USING "btree" ("status");



CREATE INDEX "idx_oauth_tokens_provider" ON "public"."oauth_tokens" USING "btree" ("provider");



CREATE INDEX "idx_profiles_whatsapp_user_id" ON "public"."profiles" USING "btree" ("whatsapp_user_id");



ALTER TABLE ONLY "public"."actions"
    ADD CONSTRAINT "actions_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."client_sessions"
    ADD CONSTRAINT "client_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."connections"
    ADD CONSTRAINT "connections_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."dedupe_keys"
    ADD CONSTRAINT "dedupe_keys_action_id_fkey" FOREIGN KEY ("action_id") REFERENCES "public"."actions"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."dedupe_keys"
    ADD CONSTRAINT "dedupe_keys_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."rules"
    ADD CONSTRAINT "rules_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."tenant_settings"
    ADD CONSTRAINT "tenant_settings_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "public"."tenants"("id") ON DELETE CASCADE;



ALTER TABLE "public"."actions" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "allow_service_all_actions" ON "public"."actions" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_audit_log" ON "public"."audit_log" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_client_sessions" ON "public"."client_sessions" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_connections" ON "public"."connections" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_dedupe_keys" ON "public"."dedupe_keys" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_rules" ON "public"."rules" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_tenant_settings" ON "public"."tenant_settings" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_tenants" ON "public"."tenants" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "allow_service_all_users" ON "public"."users" TO "service_role" USING (true) WITH CHECK (true);



ALTER TABLE "public"."audit_log" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."client_sessions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."connections" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."dedupe_keys" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."rules" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tenant_settings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tenants" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON TABLE "public"."actions" TO "anon";
GRANT ALL ON TABLE "public"."actions" TO "authenticated";
GRANT ALL ON TABLE "public"."actions" TO "service_role";



GRANT ALL ON TABLE "public"."approvals" TO "anon";
GRANT ALL ON TABLE "public"."approvals" TO "authenticated";
GRANT ALL ON TABLE "public"."approvals" TO "service_role";



GRANT ALL ON TABLE "public"."audit_log" TO "anon";
GRANT ALL ON TABLE "public"."audit_log" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_log" TO "service_role";



GRANT ALL ON TABLE "public"."automations" TO "anon";
GRANT ALL ON TABLE "public"."automations" TO "authenticated";
GRANT ALL ON TABLE "public"."automations" TO "service_role";



GRANT ALL ON TABLE "public"."client_sessions" TO "anon";
GRANT ALL ON TABLE "public"."client_sessions" TO "authenticated";
GRANT ALL ON TABLE "public"."client_sessions" TO "service_role";



GRANT ALL ON TABLE "public"."connections" TO "anon";
GRANT ALL ON TABLE "public"."connections" TO "authenticated";
GRANT ALL ON TABLE "public"."connections" TO "service_role";



GRANT ALL ON TABLE "public"."core_memory" TO "anon";
GRANT ALL ON TABLE "public"."core_memory" TO "authenticated";
GRANT ALL ON TABLE "public"."core_memory" TO "service_role";



GRANT ALL ON TABLE "public"."dedupe_keys" TO "anon";
GRANT ALL ON TABLE "public"."dedupe_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."dedupe_keys" TO "service_role";



GRANT ALL ON TABLE "public"."drafts" TO "anon";
GRANT ALL ON TABLE "public"."drafts" TO "authenticated";
GRANT ALL ON TABLE "public"."drafts" TO "service_role";



GRANT ALL ON TABLE "public"."oauth_tokens" TO "anon";
GRANT ALL ON TABLE "public"."oauth_tokens" TO "authenticated";
GRANT ALL ON TABLE "public"."oauth_tokens" TO "service_role";



GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";



GRANT ALL ON TABLE "public"."rules" TO "anon";
GRANT ALL ON TABLE "public"."rules" TO "authenticated";
GRANT ALL ON TABLE "public"."rules" TO "service_role";



GRANT ALL ON TABLE "public"."tenant_settings" TO "anon";
GRANT ALL ON TABLE "public"."tenant_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."tenant_settings" TO "service_role";



GRANT ALL ON TABLE "public"."tenants" TO "anon";
GRANT ALL ON TABLE "public"."tenants" TO "authenticated";
GRANT ALL ON TABLE "public"."tenants" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";







