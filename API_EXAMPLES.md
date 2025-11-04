# API Examples - CURL Commands

## Authentication

### Login
```bash
# Login and save token
RESPONSE=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@benefactor.local",
    "password": "ChangeMe123!"
  }')

# Extract access token
TOKEN=$(echo $RESPONSE | jq -r '.accessToken')
echo "Access Token: $TOKEN"
```

### Use Token in Subsequent Requests
```bash
# Set the token as an environment variable
export ACCESS_TOKEN="your_access_token_here"
```

## Client Management

### Create a New Client
```bash
curl -X POST http://localhost/api/clients \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Suresh",
    "lastName": "Reddy",
    "email": "suresh.reddy@example.com",
    "phone": "+919988776655",
    "status": "prospect",
    "pan": "KLMNO1234P",
    "bankAccount": "5544332211",
    "bankName": "State Bank of India",
    "bankIfsc": "SBIN0001234",
    "address": "101 MG Road",
    "city": "Hyderabad",
    "state": "Telangana",
    "postalCode": "500001",
    "country": "India",
    "dateOfBirth": "1980-03-15",
    "riskProfile": "aggressive"
  }' | jq
```

### List All Clients
```bash
curl -X GET http://localhost/api/clients \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

### Get Client by ID
```bash
CLIENT_ID="your-client-uuid"

curl -X GET http://localhost/api/clients/$CLIENT_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

### Update Client (Mark as Onboarded)
```bash
# This will trigger the welcome email workflow
curl -X PUT http://localhost/api/clients/$CLIENT_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "isOnboarded": true,
    "onboardedAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }' | jq
```

## Messaging

### Send Test Email (via MailHog)
```bash
curl -X POST http://localhost/api/messages/send \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID'",
    "channel": "email",
    "to": "client@example.com",
    "subject": "Portfolio Review Scheduled",
    "body": "Dear Client,\n\nYour portfolio review has been scheduled for next Monday at 2 PM.\n\nBest regards,\nBenefactor Wealth Team"
  }' | jq
```

Check MailHog UI at http://localhost:8025 to see the email.

### Send Test SMS (Stub)
```bash
curl -X POST http://localhost/api/messages/send \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID'",
    "channel": "sms",
    "to": "+919876543210",
    "body": "Your portfolio has been updated. Login to view details."
  }' | jq
```

## Workflows

### Manually Trigger Workflow
```bash
curl -X POST http://localhost/api/workflows/trigger \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triggerType": "client.onboarded",
    "context": {
      "clientId": "'$CLIENT_ID'",
      "email": "client@example.com",
      "firstName": "John",
      "lastName": "Doe"
    }
  }' | jq
```

## Webhooks

### Simulate Inbound Twilio SMS
```bash
curl -X POST http://localhost/api/webhooks/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=%2B919876543210" \
  -d "To=%2B911234567890" \
  -d "Body=I need help with my portfolio" \
  -d "MessageSid=SM123456789" \
  -d "AccountSid=AC123456789" | jq
```

## Health Check

### Check System Health
```bash
curl -X GET http://localhost/api/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T10:30:00.000Z",
  "database": "connected",
  "uptime": 12345.67
}
```

## Complete Workflow Example

### 1. Login
```bash
RESPONSE=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@benefactor.local","password":"ChangeMe123!"}')

TOKEN=$(echo $RESPONSE | jq -r '.accessToken')
```

### 2. Create Client
```bash
CLIENT_RESPONSE=$(curl -s -X POST http://localhost/api/clients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "TestUser",
    "lastName": "Demo",
    "email": "testuser@example.com",
    "phone": "+919999999999",
    "status": "prospect"
  }')

CLIENT_ID=$(echo $CLIENT_RESPONSE | jq -r '.id')
echo "Created client: $CLIENT_ID"
```

### 3. Onboard Client (Triggers Welcome Email)
```bash
curl -s -X PUT http://localhost/api/clients/$CLIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "isOnboarded": true
  }' | jq
```

### 4. Check MailHog for Welcome Email
```bash
# Open http://localhost:8025 in your browser
open http://localhost:8025
```

### 5. Send Custom Email
```bash
curl -s -X POST http://localhost/api/messages/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'$CLIENT_ID'",
    "channel": "email",
    "to": "testuser@example.com",
    "subject": "Welcome Follow-up",
    "body": "Thank you for onboarding with us!"
  }' | jq
```

## Tips

1. **Save your access token**: Export it as an environment variable for easier use
   ```bash
   export ACCESS_TOKEN="your_token_here"
   ```

2. **Pretty print JSON**: Pipe all responses through `jq` for readable output

3. **Debug requests**: Add `-v` flag to curl for verbose output
   ```bash
   curl -v -X GET http://localhost/api/clients ...
   ```

4. **Save responses**: Redirect output to a file
   ```bash
   curl ... > response.json
   ```

5. **Test workflows**: After onboarding a client, check MailHog (http://localhost:8025) to see the automated welcome email
