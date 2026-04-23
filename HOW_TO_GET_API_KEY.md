# How to Get Your Shop API Key

## Overview
API keys are automatically generated when you onboard a shop. You can get your API key in two ways:

## Method 1: During Shop Onboarding (Recommended)

When you onboard a new shop, the API key is automatically generated and returned in the response.

### Step 1: Onboard Your Shop
```bash
curl -X POST "http://localhost:8000/shops/onboard" \
  -H "Content-Type: application/json" \
  -d '{
    "shop": {
      "shop_name": "My Shop",
      "password": "mypassword123"
    },
    "owner": {
      "owner_name": "Owner Name"
    }
  }'
```

### Step 2: Save the API Key from Response
The response will include your API key:
```json
{
  "shop": {
    "id": 1,
    "shop_name": "My Shop",
    "shop_code": "MYSHOPA1B2",
    "api_key": "kf_abc123def456ghi789...",  // ← THIS IS YOUR API KEY
    ...
  },
  ...
}
```

**⚠️ IMPORTANT:** Save this API key securely! You won't be able to see it again unless you use Method 2.

---

## Method 2: Login with Shop Code and Password

If you already onboarded a shop but lost your API key, you can retrieve it by logging in.

### Step 1: Login with Shop Code and Password
```bash
curl -X POST "http://localhost:8000/shops/login" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_code": "MYSHOPA1B2",
    "password": "mypassword123"
  }'
```

### Step 2: Get API Key from Response
The response will include your API key:
```json
{
  "id": 1,
  "shop_name": "My Shop",
  "shop_code": "MYSHOPA1B2",
  "api_key": "kf_abc123def456ghi789...",  // ← THIS IS YOUR API KEY
  ...
}
```

---

## API Key Format

- **Prefix**: `kf_` (KiranaFlow identifier)
- **Length**: ~45 characters total
- **Example**: `kf_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`

## Using Your API Key

Once you have your API key, use it in the `X-API-Key` header for authenticated requests:

```bash
curl -X GET "http://localhost:8000/shops/me" \
  -H "X-API-Key: kf_abc123def456ghi789..."
```

## Security Best Practices

1. **Never share your API key** publicly or commit it to version control
2. **Store it securely** - Use environment variables or secure storage
3. **Rotate if compromised** - Contact support if your API key is exposed
4. **Use HTTPS in production** - Always use encrypted connections

## Example: Complete Flow

### 1. Onboard Shop
```bash
curl -X POST "http://localhost:8000/shops/onboard" \
  -H "Content-Type: application/json" \
  -d '{
    "shop": {
      "shop_name": "Test Shop",
      "password": "test123456"
    },
    "owner": {
      "owner_name": "John Doe"
    }
  }'
```

**Response:**
```json
{
  "shop": {
    "shop_code": "TESTSHA1B2",
    "api_key": "kf_xYz123AbC456DeF789GhI012JkL345MnO678PqR901StU234VwX567YzA890"
  }
}
```

### 2. Use API Key
```bash
curl -X GET "http://localhost:8000/shops/me" \
  -H "X-API-Key: kf_xYz123AbC456DeF789GhI012JkL345MnO678PqR901StU234VwX567YzA890"
```

## Troubleshooting

### "Invalid or missing API key"
- Check that you're using the correct API key
- Ensure the `X-API-Key` header is spelled correctly
- Verify your shop is active (`is_active: true`)

### "Shop is not active"
- Your shop account may have been deactivated
- Contact support to reactivate your shop

### Forgot Shop Code?
- Check your onboarding email/records
- Contact support with your shop name and details
