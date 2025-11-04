import { MigrationInterface, QueryRunner } from 'typeorm';

export class InitialSchema1700000000001 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Enable pgcrypto extension for encryption
    await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS "pgcrypto"`);
    await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`);

    // Create roles table
    await queryRunner.query(`
      CREATE TABLE "roles" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "name" varchar NOT NULL UNIQUE,
        "description" text,
        "permissions" jsonb DEFAULT '{}',
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now()
      )
    `);

    // Create users table
    await queryRunner.query(`
      CREATE TABLE "users" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "email" varchar NOT NULL UNIQUE,
        "password" varchar NOT NULL,
        "first_name" varchar NOT NULL,
        "last_name" varchar NOT NULL,
        "status" varchar DEFAULT 'active',
        "role_id" uuid NOT NULL,
        "refresh_token" varchar,
        "last_login" timestamp,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_user_role" FOREIGN KEY ("role_id") REFERENCES "roles"("id")
      )
    `);

    // Create clients table with encrypted columns
    await queryRunner.query(`
      CREATE TABLE "clients" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "first_name" varchar NOT NULL,
        "last_name" varchar NOT NULL,
        "email" varchar NOT NULL UNIQUE,
        "phone" varchar,
        "alternate_phone" varchar,
        "pan" bytea,
        "bank_account" bytea,
        "bank_name" varchar,
        "bank_ifsc" varchar,
        "address" text,
        "city" varchar,
        "state" varchar,
        "postal_code" varchar,
        "country" varchar,
        "date_of_birth" date,
        "status" varchar DEFAULT 'prospect',
        "risk_profile" varchar,
        "assigned_rm_id" uuid,
        "is_onboarded" boolean DEFAULT false,
        "onboarded_at" timestamp,
        "notes" text,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_client_rm" FOREIGN KEY ("assigned_rm_id") REFERENCES "users"("id")
      )
    `);

    // Create consents table
    await queryRunner.query(`
      CREATE TABLE "consents" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid NOT NULL,
        "type" varchar NOT NULL,
        "status" varchar DEFAULT 'pending',
        "granted_at" timestamp,
        "revoked_at" timestamp,
        "notes" text,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_consent_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE
      )
    `);

    // Create portfolio_links table
    await queryRunner.query(`
      CREATE TABLE "portfolio_links" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid NOT NULL,
        "external_portfolio_id" varchar NOT NULL,
        "platform_name" varchar NOT NULL,
        "metadata" jsonb,
        "is_active" boolean DEFAULT true,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_portfolio_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE
      )
    `);

    // Create contacts table
    await queryRunner.query(`
      CREATE TABLE "contacts" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid NOT NULL,
        "method" varchar NOT NULL,
        "direction" varchar NOT NULL,
        "subject" varchar NOT NULL,
        "notes" text NOT NULL,
        "contacted_at" timestamp NOT NULL,
        "contacted_by" varchar,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_contact_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE
      )
    `);

    // Create messages table
    await queryRunner.query(`
      CREATE TABLE "messages" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid NOT NULL,
        "channel" varchar NOT NULL,
        "direction" varchar NOT NULL,
        "status" varchar DEFAULT 'pending',
        "from" varchar,
        "to" varchar,
        "subject" varchar,
        "body" text NOT NULL,
        "metadata" jsonb,
        "sent_at" timestamp,
        "delivered_at" timestamp,
        "failed_at" timestamp,
        "error_message" text,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_message_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE
      )
    `);

    // Create tasks table
    await queryRunner.query(`
      CREATE TABLE "tasks" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid,
        "title" varchar NOT NULL,
        "description" text,
        "status" varchar DEFAULT 'todo',
        "priority" varchar DEFAULT 'medium',
        "assigned_to_id" uuid,
        "due_date" timestamp,
        "completed_at" timestamp,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_task_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_task_assignee" FOREIGN KEY ("assigned_to_id") REFERENCES "users"("id")
      )
    `);

    // Create documents table
    await queryRunner.query(`
      CREATE TABLE "documents" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "client_id" uuid NOT NULL,
        "name" varchar NOT NULL,
        "type" varchar NOT NULL,
        "file_path" varchar NOT NULL,
        "file_size" int NOT NULL,
        "mime_type" varchar NOT NULL,
        "uploaded_by" varchar,
        "notes" text,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_document_client" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE CASCADE
      )
    `);

    // Create workflows table
    await queryRunner.query(`
      CREATE TABLE "workflows" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "name" varchar NOT NULL,
        "description" text,
        "definition" jsonb NOT NULL,
        "is_active" boolean DEFAULT true,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now()
      )
    `);

    // Create workflow_runs table
    await queryRunner.query(`
      CREATE TABLE "workflow_runs" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "workflow_id" uuid NOT NULL,
        "status" varchar DEFAULT 'pending',
        "context" jsonb,
        "results" jsonb,
        "error_message" text,
        "started_at" timestamp,
        "completed_at" timestamp,
        "created_at" timestamp DEFAULT now(),
        "updated_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_run_workflow" FOREIGN KEY ("workflow_id") REFERENCES "workflows"("id") ON DELETE CASCADE
      )
    `);

    // Create audit_logs table
    await queryRunner.query(`
      CREATE TABLE "audit_logs" (
        "id" uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        "user_id" uuid,
        "action" varchar NOT NULL,
        "entity_type" varchar NOT NULL,
        "entity_id" varchar,
        "changes" jsonb,
        "ip_address" varchar,
        "user_agent" varchar,
        "created_at" timestamp DEFAULT now(),
        CONSTRAINT "fk_audit_user" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL
      )
    `);

    // Create indexes for better performance
    await queryRunner.query(`CREATE INDEX "idx_users_email" ON "users"("email")`);
    await queryRunner.query(`CREATE INDEX "idx_clients_email" ON "clients"("email")`);
    await queryRunner.query(`CREATE INDEX "idx_clients_status" ON "clients"("status")`);
    await queryRunner.query(`CREATE INDEX "idx_messages_client" ON "messages"("client_id")`);
    await queryRunner.query(`CREATE INDEX "idx_tasks_client" ON "tasks"("client_id")`);
    await queryRunner.query(`CREATE INDEX "idx_tasks_assignee" ON "tasks"("assigned_to_id")`);
    await queryRunner.query(
      `CREATE INDEX "idx_audit_logs_entity" ON "audit_logs"("entity_type", "entity_id")`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP TABLE IF EXISTS "audit_logs" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "workflow_runs" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "workflows" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "documents" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "tasks" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "messages" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "contacts" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "portfolio_links" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "consents" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "clients" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "users" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "roles" CASCADE`);
    await queryRunner.query(`DROP EXTENSION IF EXISTS "pgcrypto"`);
    await queryRunner.query(`DROP EXTENSION IF EXISTS "uuid-ossp"`);
  }
}
