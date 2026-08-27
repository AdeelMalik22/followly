# WhatsApp Integration Setup Guide

## Prerequisites

1. Meta Business Account
2. Meta Developer Account
3. WhatsApp Business API access

## Setup Steps

### 1. Create Meta App

1. Go to https://developers.facebook.com/apps
2. Click "Create App"
3. Select "Business" type
4. Fill in app details

### 2. Add WhatsApp Product

1. In app dashboard, click "Add Product"
2. Select "WhatsApp" and click "Set Up"
3. Select or create a WhatsApp Business Account

### 3. Get Credentials

**Phone Number ID:**
- Go to WhatsApp > Getting Started
- Copy the "Phone number ID" (starts with numbers like 123456789012345)

**Access Token:**
- Go to WhatsApp > Getting Started
- Copy the temporary access token (starts with EAA...)
- For production, generate a permanent token from System Users

**Verify Token:**
- Create your own random string (e.g., "my_secure_verify_token_12345")

### 4. Configure Environment Variables

Add to `.env`:

```bash
WHATSAPP_VERIFY_TOKEN=my_secure_verify_token_12345
WHATSAPP_APP_SECRET=your_meta_app_secret
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAA...
```

### 5. Setup Webhook

**Webhook URL:** `https://your-domain.com/api/v1/whatsapp/webhook`

**Steps:**
1. Go to WhatsApp > Configuration
2. Click "Edit" next to Webhook
3. Enter your webhook URL
4. Enter your verify token (same as WHATSAPP_VERIFY_TOKEN)
5. Click "Verify and Save"

**Subscribe to fields:**
- Check "messages" field
- Save

### 6. Testing Locally with ngrok

For local development:

```bash
# Install ngrok
npm install -g ngrok

# Start your FastAPI server
uvicorn app.main:app --reload --port 8000

# In another terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Use this URL in Meta webhook configuration:
# https://abc123.ngrok.io/api/v1/whatsapp/webhook
```

### 7. Test the Integration

**Send a test message:**
1. Send a WhatsApp message to your test number
2. Check server logs for incoming webhook
3. Check database for created Lead and Conversation

**Use the send endpoint:**
```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "1234567890",
    "message": "Hello from Followly!"
  }'
```

## Webhook Payload Example

When a user sends a message, Meta sends this to your webhook:

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "15551234567",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "contacts": [{
          "profile": {
            "name": "John Doe"
          },
          "wa_id": "1234567890"
        }],
        "messages": [{
          "from": "1234567890",
          "id": "wamid.XXX",
          "timestamp": "1660000000",
          "text": {
            "body": "Hello, I need an appointment"
          },
          "type": "text"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

## Business Settings Storage

Each business stores WhatsApp credentials in the `settings` JSONB column:

```python
# Store credentials when business connects WhatsApp
business.settings = {
    "whatsapp_phone_id": "123456789012345",
    "whatsapp_access_token": "EAA...",
    ...
}
```

## API Endpoints

### GET /api/v1/whatsapp/webhook
Webhook verification endpoint (called by Meta during setup)

**Query Parameters:**
- `hub.mode=subscribe`
- `hub.verify_token=<your_verify_token>`
- `hub.challenge=<random_string>`

**Response:** Returns the challenge string

### POST /api/v1/whatsapp/webhook
Incoming message handler

**Body:** WhatsApp webhook payload (see example above)

**Flow:**
1. Parse incoming message
2. Find business by phone_number_id
3. Get or create Lead
4. Get or create Conversation
5. Save message to database
6. Update lead status
7. (TODO) Process with AI agent and respond

### POST /api/v1/whatsapp/send
Manual send endpoint for testing

**Body:**
```json
{
  "to": "1234567890",
  "message": "Your message text"
}
```

## Troubleshooting

### Webhook not receiving messages
- Check webhook URL is HTTPS (required by Meta)
- Verify token matches in both .env and Meta config
- Check "messages" field is subscribed in Meta webhook config
- Check ngrok is running (for local dev)

### Send message fails
- Verify WHATSAPP_ACCESS_TOKEN is valid
- Check WHATSAPP_PHONE_NUMBER_ID is correct
- Ensure recipient number is in E.164 format (e.g., 1234567890)
- For test numbers, add them in Meta dashboard first

### Business not found for incoming message
- Ensure business.settings contains whatsapp_phone_id
- Check phone_number_id in webhook matches stored value

## Next Steps

After WhatsApp integration is working:
1. Implement conversation engine with AI agent
2. Add automatic response to incoming messages
3. Implement conversation context and tool calling
4. Add message templates for common responses
