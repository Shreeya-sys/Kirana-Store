# Multi-Tenant Shop Onboarding System

## Overview
The KiranaFlow system now supports multi-tenancy with shop onboarding via API keys. Each shop gets a unique API key for authentication and can have owner details stored.

## User Hierarchy

The system implements a 4-tier hierarchy:

```
Root Admin (Internal API)
    ↓
Tenant Admin (Shop Owner) - Created automatically during onboarding
    ↓
Staff (Shop Employees) - Created by tenant admin
    ↓
Customer (Shop Customers) - Created by tenant admin or staff
```

**See `USER_HIERARCHY.md` for complete role-based access control documentation.**

## Database Models

### Shop Model
- `id`: Primary key
- `shop_name`: Name of the shop
- `shop_code`: Unique identifier (auto-generated from shop name)
- `api_key`: Unique API key for authentication (auto-generated)
- `hashed_password`: Encrypted password for shop authentication
- `address`, `city`, `state`, `pincode`: Location details
- `gst_number`: GST registration number
- `phone`: Phone number (optional)
- `email`: Email address (optional)
- `email_password`: Encrypted password for email account (optional)
- `is_active`: Shop status
- `created_at`, `updated_at`: Timestamps

### Owner Model
- `id`: Primary key
- `shop_id`: Foreign key to Shop (one-to-one relationship)
- `owner_name`: Name of the shop owner
- `phone`: Owner's phone number (optional)
- `email`: Owner's email (optional)
- `aadhaar_number`: Aadhaar card number
- `pan_number`: PAN card number
- `address`: Owner's address
- `created_at`, `updated_at`: Timestamps

### User Model (Updated)
- Added `shop_id` foreign key to link users to shops
- `tenant_id` is deprecated but kept for backward compatibility

## API Endpoints

### 1. Shop Onboarding
**POST** `/shops/onboard`

Onboard a new shop with owner details. This endpoint:
- Creates a shop record
- Generates a unique `shop_code` from shop name
- Generates a secure API key
- Creates owner record linked to the shop
- **Automatically creates a Tenant Admin User account** for immediate login access
  - Username: `shop_code` (e.g., "SHREEYAB3F2")
  - Password: Same as shop password
  - Role: `tenant_admin` (manages their shop)
  - Linked to shop via `shop_id`
- Returns shop and owner details with API key

**🔑 Login Integration**: After onboarding, the tenant admin can immediately login using:
- **User Login**: `POST /token` (username=`shop_code`, password=`shop_password`)
- **Shop Login**: `POST /shops/login` (shop_code + password)
- **API Key**: Use `X-API-Key` header

**After login, tenant admin can:**
- Create staff users via `POST /tenant/staff`
- Create customers via `POST /customers/`
- Manage their shop resources

**Validation Rules:**
- `password` is required (minimum 6 characters)
- `shop_name` is required

**Request Body:**
```json
{
  "shop": {
    "shop_name": "Shreeya Kirana Store",
    "password": "securepassword123",
    "address": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "gst_number": "27ABCDE1234F1Z5",
    "phone": "+919876543210",
    "email": "shop@example.com",
    "email_password": "emailpassword123"
  },
```

  "owner": {
    "owner_name": "Shreeya Patel",
    "phone": "+919876543210",
    "email": "owner@example.com",
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "address": "123 Main Street, Mumbai"
  }
}
```

**Response:**
```json
{
  "shop": {
    "id": 1,
    "shop_name": "Shreeya Kirana Store",
    "shop_code": "SHREEYAB3F2",
    "api_key": "kf_abc123...",
    "address": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "gst_number": "27ABCDE1234F1Z5",
    "phone": "+919876543210",
    "email": "shop@example.com",
    "is_active": true,
    "created_at": "2026-01-24T10:30:00"
    },
    "note": "email_password is not returned in response for security"
  },
  "owner": {
    "id": 1,
    "shop_id": 1,
    "owner_name": "Shreeya Patel",
    "phone": "+919876543210",
    "email": "owner@example.com",
    "aadhaar_number": "1234 5678 9012",
    "pan_number": "ABCDE1234F",
    "address": "123 Main Street, Mumbai",
    "created_at": "2026-01-24T10:30:00"
  },
  "message": "Shop onboarded successfully! You can now login using:\n- Username: SHREEYAB3F2, Password: your_shop_password (via POST /token)\n- Shop Code: SHREEYAB3F2, Password: your_shop_password (via POST /shops/login)\n- API Key: kf_abc123... (via X-API-Key header)\n\nPlease save your API key securely."
}
```

### 2. Get Shop Information
**GET** `/shops/me`

Get current shop information using API key authentication. This endpoint returns the authenticated shop's details including shop code, API key, and contact information.

**Authentication:**
- Requires API key in the request header

**Headers:**
```
X-API-Key: kf_abc123...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "shop_name": "Shreeya Kirana Store",
  "shop_code": "SHREEYAB3F2",
  "api_key": "kf_abc123def456ghi789",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "gst_number": "27ABCDE1234F1Z5",
  "phone": "+919876543210",
  "email": "shop@example.com",
  "is_active": true,
  "created_at": "2026-01-24T10:30:00"
}
```

**Error Responses:**

- **401 Unauthorized** - Missing or invalid API key:
```json
{
  "detail": "Invalid or missing API key"
}
```

- **403 Forbidden** - Shop is inactive:
```json
{
  "detail": "Shop is not active"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/shops/me" \
  -H "X-API-Key: kf_abc123def456ghi789"
```

**Python Example:**
```python
import requests

headers = {
    "X-API-Key": "kf_abc123def456ghi789"
}

response = requests.get("http://localhost:8000/shops/me", headers=headers)
shop_data = response.json()
print(shop_data)
```

**JavaScript/Fetch Example:**
```javascript
fetch('http://localhost:8000/shops/me', {
  method: 'GET',
  headers: {
    'X-API-Key': 'kf_abc123def456ghi789'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### 3. Get Owner Information
**GET** `/shops/{shop_id}/owner`

Get owner information for the authenticated shop. The shop_id must match the authenticated shop.

**Headers:**
```
X-API-Key: kf_abc123...
```

**Response:**
```json
{
  "id": 1,
  "shop_id": 1,
  "owner_name": "Shreeya Patel",
  "phone": "+919876543210",
  ...
}
```

## API Key Authentication

API keys are used for shop-level authentication. Include the API key in the request header:

```
X-API-Key: kf_abc123...
```

The `verify_api_key` dependency validates the API key and returns the authenticated shop object.

## Usage Example

### 1. Onboard a Shop (with Phone)
```bash
curl -X POST "http://localhost:8000/shops/onboard" \
  -H "Content-Type: application/json" \
  -d '{
    "shop": {
      "shop_name": "Shreeya Kirana Store",
      "password": "securepassword123",
      "address": "123 Main Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400001",
      "gst_number": "27ABCDE1234F1Z5",
      "phone": "+919876543210",
      "email": "shop@example.com",
      "email_password": "emailpassword123"
    },
    "owner": {
      "owner_name": "Shreeya Patel",
      "phone": "+919876543210",
      "email": "owner@example.com",
      "aadhaar_number": "1234 5678 9012",
      "pan_number": "ABCDE1234F",
      "address": "123 Main Street, Mumbai"
    }
  }'
```

### 1b. Onboard a Shop (with Email only - no phone)
```bash
curl -X POST "http://localhost:8000/shops/onboard" \
  -H "Content-Type: application/json" \
  -d '{
    "shop": {
      "shop_name": "Email Only Shop",
      "password": "securepassword123",
      "address": "456 Main Street",
      "city": "Delhi",
      "state": "Delhi",
      "pincode": "110001",
      "email": "shop@example.com",
      "email_password": "emailpassword123"
    },
    "owner": {
      "owner_name": "Shreeya Patel",
      "phone": "+919876543210",
      "email": "owner@example.com",
      "aadhaar_number": "1234 5678 9012",
      "pan_number": "ABCDE1234F",
      "address": "123 Main Street, Mumbai"
    }
  }'
```


### 2. Get Shop Information (Using API Key)
```bash
curl -X GET "http://localhost:8000/shops/me" \
  -H "X-API-Key: kf_abc123def456ghi789"
```

**Expected Response:**
```json
{
  "id": 1,
  "shop_name": "Shreeya Kirana Store",
  "shop_code": "SHREEYAB3F2",
  "api_key": "kf_abc123def456ghi789",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "gst_number": "27ABCDE1234F1Z5",
  "phone": "+919876543210",
  "email": "shop@example.com",
  "is_active": true,
  "created_at": "2026-01-24T10:30:00"
}
```

### 3. Shop Login (Get API Key)
**POST** `/shops/login`

Login using shop code and password to retrieve your API key.

**Request Body:**
```json
{
  "shop_code": "SHREEYAB3F2",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "id": 1,
  "shop_name": "Shreeya Kirana Store",
  "shop_code": "SHREEYAB3F2",
  "api_key": "kf_abc123def456ghi789",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001",
  "gst_number": "27ABCDE1234F1Z5",
  "phone": "+919876543210",
  "email": "shop@example.com",
  "is_active": true,
  "created_at": "2026-01-24T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/shops/login" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_code": "SHREEYAB3F2",
    "password": "securepassword123"
  }'
```

## Security Notes

1. **Password Storage**: Shop passwords are hashed using SHA-256 pre-hashing + bcrypt before storage
3. **Email Password Storage**: Email passwords are also encrypted using the same SHA-256 + bcrypt method
4. **Password Requirements**: Minimum 6 characters for shop password (can be extended)
5. **API Key Storage**: API keys are generated using `secrets.token_urlsafe()` for cryptographically secure random generation
6. **API Key Format**: Keys are prefixed with `kf_` for identification
7. **Shop Code**: Auto-generated from shop name with random suffix to ensure uniqueness
8. **One-to-One Relationship**: Each shop has exactly one owner
9. **API Key Validation**: Only active shops can authenticate with their API keys
10. **Authentication Options**: Shops can authenticate using either:
    - Shop code + password (via `/shops/login` endpoint)
    - API key (via `X-API-Key` header)
11. **Seamless Login Integration**: When a shop is onboarded, a **Tenant Admin User account** is **automatically and immediately created** with:
    - Username: The shop's `shop_code` (e.g., "SHREEYAB3F2")
    - Password: Same as the shop password (unified authentication)
    - Role: `tenant_admin` (shop owner manages their shop)
    - Linked to the shop via `shop_id`
    - **This is a fundamental requirement** - shop onboarding fails if user creation fails
    - **Immediate access**: Tenant admin can login via `/token` endpoint right after onboarding
12. **User Hierarchy**: 
    - **Root Admin** (`root_admin`): Manages all tenants via `/admin/*` endpoints
    - **Tenant Admin** (`tenant_admin`): Manages their shop, creates staff/customers
    - **Staff** (`staff`): Shop employees, can manage customers
    - **Customer** (`customer`): Shop customers (limited access)
13. **Unified Authentication**: The same credentials work for both:
    - User login: `POST /token` (username=`shop_code`, password=`shop_password`)
    - Shop login: `POST /shops/login` (shop_code + password)
    - This provides a seamless experience - one onboarding, multiple login methods
14. **Email Integration**: Email password is stored encrypted and can be used for email service integration (Gmail, etc.)

## Database Migration

When you restart the server, the new tables (`shops` and `owners`) will be automatically created. Existing data will remain intact.

## Next Steps

✅ **Completed:**
1. ✅ Updated existing endpoints to filter by `shop_id` when using tenant authentication
2. ✅ Linked items, invoices, invoice_items, ledgers, and stock_adjustments to shops
3. ✅ Added shop-level user management (tenant admin can create staff and customers)
4. ✅ Implemented shop-level permissions and roles (RBAC with root_admin, tenant_admin, staff, customer)

**Future Enhancements:**
- Add API key authentication support for items/invoices endpoints (currently uses JWT only)
- Add bulk operations for items and invoices
- Add reporting and analytics per shop
