# Benefactor Wealth CRM - Secure Financial Advisory Platform

A production-ready, local-first Customer Relationship Management system for financial advisory firms. Built with security, compliance, and data sovereignty in mind.

## 🚀 Features

- **Secure Authentication**: JWT with refresh tokens, Argon2 password hashing
- **Role-Based Access Control (RBAC)**: SuperAdmin, Admin, RM, Compliance roles
- **Audit Logging**: Complete audit trail for all CUD operations
- **PII Encryption**: Client sensitive data encrypted with AES-256
- **Multi-Channel Messaging**: Email (SMTP), SMS/WhatsApp (Twilio)
- **Workflow Automation**: Trigger-based automation engine
- **Client Management**: Complete CRM functionality with portfolio tracking
- **Backup & Restore**: Encrypted database backups with GPG

## 📋 Prerequisites

- **Docker** & **Docker Compose**
- **Node.js** 18+ (for local development)
- **GPG** (for encrypted backups)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Nginx     │────▶│   Backend   │────▶│  PostgreSQL  │
│  (Proxy)    │     │  (NestJS)   │     │  (Encrypted) │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────▼────┐  ┌────▼─────┐
              │  Redis   │  │ MailHog  │
              └──────────┘  └──────────┘

┌─────────────┐
│  Frontend   │
│  (React)    │
└─────────────┘
```

### Stack

**Backend:**
- NestJS + TypeScript
- TypeORM + PostgreSQL
- JWT Authentication
- Argon2 Password Hashing
- Redis for caching

**Frontend:**
- React + TypeScript
- Vite
- Tailwind CSS
- Zustand for state management

**Infrastructure:**
- Docker Compose
- Nginx reverse proxy
- PostgreSQL with pgcrypto
- Redis
- MailHog (dev email testing)

## 🚀 Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
cd Trading

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and set **secure values** for:

```bash
# Database
POSTGRES_PASSWORD=your_secure_db_password

# JWT Secrets (generate random 32+ character strings)
JWT_SECRET=your_jwt_secret_min_32_chars
JWT_REFRESH_SECRET=your_jwt_refresh_secret_min_32_chars

# Encryption Key (generate a 64 character hex string for AES-256)
# Generate with: openssl rand -hex 32
ENCRYPTION_KEY=your_64_char_hex_encryption_key

# Backup Passphrase
BACKUP_GPG_PASSPHRASE=your_backup_encryption_password
```

### 3. Start Services

```bash
# Build and start all services
docker compose up --build -d

# Check service status
docker compose ps
```

### 4. Run Migrations and Seed Data

```bash
# Run database migrations
docker compose exec backend npm run migrate

# Seed initial data (creates admin user and demo clients)
docker compose exec backend npm run seed
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost/api
- **MailHog UI**: http://localhost:8025
- **Health Check**: http://localhost/api/health

**Default Admin Credentials:**
```
Email: admin@benefactor.local
Password: ChangeMe123!
```

⚠️ **IMPORTANT**: Change the default password immediately!

## 📁 Project Structure

```
.
├── backend/
│   ├── src/
│   │   ├── auth/              # Authentication module
│   │   ├── users/             # User management
│   │   ├── clients/           # Client CRM
│   │   ├── messages/          # Multi-channel messaging
│   │   │   ├── adapters/      # SMTP, Twilio adapters
│   │   │   └── interfaces/    # Message adapter interface
│   │   ├── workflows/         # Automation engine
│   │   ├── webhooks/          # Inbound webhook handlers
│   │   ├── audit/             # Audit logging
│   │   ├── common/            # Guards, interceptors, utils
│   │   │   ├── guards/        # JWT, RBAC guards
│   │   │   ├── interceptors/  # Audit logging
│   │   │   └── utils/         # Encryption utilities
│   │   └── database/
│   │       ├── migrations/    # TypeORM migrations
│   │       └── seeds/         # Seed data scripts
│   ├── Dockerfile
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   ├── stores/           # Zustand stores
│   │   └── types/            # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── backup.sh             # Encrypted backup script
│   ├── restore.sh            # Restore from backup
│   └── init-db.sql           # Database initialization
├── nginx/
│   └── nginx.conf            # Reverse proxy config
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔐 Security

### Encryption

**PII Data Encryption:**
- Sensitive fields (PAN, bank accounts) are encrypted using AES-256
- Encryption key stored in `ENCRYPTION_KEY` environment variable
- **Production**: Store encryption keys in HashiCorp Vault or AWS Secrets Manager

```typescript
// Example: Encrypting client PAN
import { EncryptionUtil } from './common/utils/encryption.util';

// Encrypt before saving
const encryptedPAN = EncryptionUtil.encrypt('ABCDE1234F');

// Decrypt when reading
const decryptedPAN = EncryptionUtil.decrypt(encryptedPAN);
```

**Key Management Recommendations:**
1. **Development**: Use `.env` file (never commit)
2. **Production**: Use secrets management (Vault, AWS Secrets Manager)
3. **Implement key rotation** with versioning
4. **Keep backup of old keys** for decryption during rotation

### Password Security

- Passwords hashed with **Argon2** (winner of Password Hashing Competition)
- Configurable work factors
- Salt automatically generated per password

### Audit Logging

All Create, Update, and Delete operations are automatically logged:

```sql
SELECT * FROM audit_logs
WHERE entity_type = 'Client'
  AND user_id = 'user-uuid'
ORDER BY created_at DESC;
```

### RBAC Permissions

| Role        | Permissions                                    |
|-------------|------------------------------------------------|
| SuperAdmin  | Full system access                             |
| Admin       | Manage users, clients, workflows               |
| RM          | View/create/edit clients, messages, tasks      |
| Compliance  | View clients, view audit logs (read-only)      |

### Disk Encryption

For production deployments, enable full disk encryption:

- **Linux**: LUKS (`cryptsetup`)
- **Windows**: BitLocker
- **macOS**: FileVault

## 📧 Messaging Connectors

### SMTP (Email)

**Development**: Configured for MailHog (included in Docker Compose)
- No credentials needed
- View emails at http://localhost:8025

**Production**: Configure SMTP settings in `.env`
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### Twilio (SMS/WhatsApp)

**Current**: Stub implementation (logs only, doesn't send)

**To Enable**:
1. Sign up for Twilio account
2. Configure in `.env`:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```
3. Uncomment Twilio client code in `backend/src/messages/adapters/twilio.adapter.ts`
4. Restart backend: `docker compose restart backend`

**Webhook Endpoint**: `POST /api/webhooks/twilio`

### Adding Custom Connectors

1. Implement the `MessageAdapter` interface:
```typescript
// backend/src/messages/interfaces/message-adapter.interface.ts
export interface MessageAdapter {
  send(dto: SendMessageDto): Promise<{ success: boolean; messageId?: string }>;
  parseInbound(payload: any): Promise<ParsedMessage>;
}
```

2. Register in `MessagesService`
3. Update connector selection logic

## 🔄 Workflow Automation

Workflows execute actions based on triggers:

```json
{
  "trigger": {
    "type": "client.onboarded"
  },
  "actions": [
    {
      "type": "send_email",
      "config": {
        "to": "{{email}}",
        "subject": "Welcome to Benefactor Wealth",
        "body": "Dear {{firstName}} {{lastName}},..."
      }
    }
  ]
}
```

**Supported Triggers:**
- `client.onboarded`
- `task.completed`
- (Extend as needed)

**Supported Actions:**
- `send_email`
- `send_sms`
- `create_task`
- (Extend as needed)

**Trigger Workflows Programmatically:**
```typescript
await workflowsService.triggerWorkflows('client.onboarded', {
  clientId: client.id,
  email: client.email,
  firstName: client.firstName,
  lastName: client.lastName,
});
```

## 💾 Backup & Restore

### Create Encrypted Backup

```bash
./scripts/backup.sh backup-$(date +%Y%m%d-%H%M%S).sql.gpg
```

Backups are stored in `./backups/` and encrypted with AES256 using your `BACKUP_GPG_PASSPHRASE`.

### Restore from Backup

```bash
./scripts/restore.sh backups/backup-20241201-103000.sql.gpg
```

⚠️ **Warning**: This will replace the current database!

### Automated Backups

Add to crontab for daily backups:
```bash
0 2 * * * cd /path/to/Trading && ./scripts/backup.sh backup-$(date +\%Y\%m\%d).sql.gpg
```

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
npm test

# With coverage
npm run test:cov
```

### Run E2E Tests

```bash
cd backend
npm run test:e2e
```

## 📊 API Documentation

### Authentication

#### Login
```bash
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@benefactor.local",
    "password": "ChangeMe123!"
  }'
```

Response:
```json
{
  "accessToken": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "admin@benefactor.local",
    "firstName": "Admin",
    "lastName": "User",
    "role": "Admin"
  }
}
```

### Clients

#### Create Client
```bash
curl -X POST http://localhost/api/clients \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "phone": "+919876543210",
    "status": "prospect",
    "pan": "ABCDE1234F",
    "bankAccount": "1234567890",
    "bankName": "HDFC Bank",
    "bankIfsc": "HDFC0001234"
  }'
```

#### List Clients
```bash
curl -X GET http://localhost/api/clients \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Messages

#### Send Email
```bash
curl -X POST http://localhost/api/messages/send \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "client-uuid",
    "channel": "email",
    "to": "client@example.com",
    "subject": "Portfolio Update",
    "body": "Your portfolio has been updated..."
  }'
```

### Workflows

#### Trigger Workflow
```bash
curl -X POST http://localhost/api/workflows/trigger \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triggerType": "client.onboarded",
    "context": {
      "clientId": "client-uuid",
      "email": "client@example.com",
      "firstName": "John",
      "lastName": "Doe"
    }
  }'
```

## 📦 Postman Collection

Import `postman_collection.json` into Postman for a complete API collection with pre-configured requests.

## 🛠️ Development

### Running Locally (without Docker)

**Backend:**
```bash
cd backend
npm install
npm run start:dev
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database**: You'll still need Docker for PostgreSQL and Redis.

### Hot Reload

Both backend and frontend support hot reload in development mode.

## 🐛 Troubleshooting

### Backend won't start
- Check `.env` file exists and has all required variables
- Ensure PostgreSQL is healthy: `docker compose ps postgres`
- View logs: `docker compose logs backend`

### Frontend can't connect to API
- Check CORS settings in backend `.env`
- Ensure nginx is running: `docker compose ps nginx`
- Check `VITE_API_URL` in frontend `.env`

### Migrations fail
- Ensure database is running: `docker compose up postgres -d`
- Reset database: `docker compose down -v && docker compose up -d`
- Re-run migrations: `docker compose exec backend npm run migrate`

### Can't access MailHog
- Ensure MailHog is running: `docker compose ps mailhog`
- Access directly: http://localhost:8025

## 🔒 Production Deployment Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secrets (32+ characters)
- [ ] Generate encryption key: `openssl rand -hex 32`
- [ ] Set up Vault/Secrets Manager for keys
- [ ] Enable full disk encryption
- [ ] Configure production SMTP (not MailHog)
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure backup automation
- [ ] Test backup/restore procedures
- [ ] Enable monitoring/logging
- [ ] Review RBAC permissions
- [ ] Audit encryption implementation
- [ ] Set up key rotation schedule
- [ ] Document disaster recovery plan

## 📄 License

Proprietary - Benefactor Wealth

## 🤝 Support

For issues or questions, contact your system administrator or refer to the internal documentation wiki.

---

**Built with ❤️ for secure, compliant financial services**
