# User Hierarchy and Role-Based Access Control

## Overview
The system implements a 4-tier hierarchy for multi-tenant management:

```
Root Admin (Internal API)
    ↓
Tenant Admin (Shop Owner)
    ↓
Staff (Shop Employees)
    ↓
Customer (Shop Customers)
```

## Role Hierarchy

### 1. Root Admin (`root_admin`)
- **Purpose**: Manages all tenants/shops via internal API
- **Access**: Full system access, can manage all shops, users, and data
- **Endpoints**: `/admin/*` (internal API)
- **Creation**: Must be created manually (not via shop onboarding)
- **shop_id**: `NULL` (not linked to any specific shop)

### 2. Tenant Admin (`tenant_admin`)
- **Purpose**: Manages their own shop/tenant
- **Access**: 
  - Full access to their own shop
  - Can create/manage staff users
  - Can create/manage customers
  - Cannot access other shops
- **Creation**: Automatically created during shop onboarding
  - Username: `shop_code` (e.g., "SHREEYAB3F2")
  - Password: Same as shop password
  - Role: `tenant_admin`
  - Linked to shop via `shop_id`
- **Endpoints**: `/tenant/*`, `/customers/*`

### 3. Staff (`staff`)
- **Purpose**: Shop employees working under tenant admin
- **Access**:
  - Access to their shop's resources
  - Can manage customers
  - Cannot create users
  - Cannot access admin functions
- **Creation**: Created by tenant admin via `/tenant/staff`
- **shop_id**: Must be linked to a shop

### 4. Customer (`customer`)
- **Purpose**: Shop customers
- **Access**: 
  - Limited access (typically read-only for their own data)
  - Can view their own invoices, ledger, etc.
- **Creation**: Created by tenant admin or staff via `/customers/`
- **shop_id**: Must be linked to a shop

## Authentication Flow

### Root Admin Login
```bash
# Root admin logs in via /token endpoint
curl -X POST 'http://127.0.0.1:8000/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=root_admin&password=root_password'
```

### Tenant Admin Login
```bash
# Tenant admin logs in using shop_code as username
curl -X POST 'http://127.0.0.1:8000/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=SHREEYAB3F2&password=shop_password'
```

### Staff Login
```bash
# Staff logs in with their username
curl -X POST 'http://127.0.0.1:8000/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=staff_username&password=staff_password'
```

## API Endpoints by Role

### Root Admin Endpoints (`/admin/*`)
- `GET /admin/shops` - List all shops
- `GET /admin/users` - List all users
- `POST /users/` - Create any user (root_admin, tenant_admin, staff, customer)

### Tenant Admin Endpoints (`/tenant/*`)
- `GET /tenant/staff` - List all staff for their shop
- `POST /tenant/staff` - Create staff user for their shop
- `POST /customers/` - Create customer
- `GET /customers/` - List customers
- `GET /customers/{customer_id}` - Get customer details
- `GET /shops/me` - Get their shop info (via API key)
- `POST /shops/login` - Shop login

### Staff Endpoints
- `POST /customers/` - Create customer
- `GET /customers/` - List customers
- `GET /customers/{customer_id}` - Get customer details
- All shop resource endpoints (items, invoices, etc.)

### Customer Endpoints
- `GET /customers/me` - Get own customer info (if implemented)
- `GET /invoices/me` - Get own invoices (if implemented)
- `GET /ledger/me` - Get own ledger (if implemented)

## Shop Onboarding Flow

When a shop is onboarded via `POST /shops/onboard`:

1. **Shop Record** is created
2. **Owner Record** is created
3. **Tenant Admin User** is automatically created:
   - Username: `shop_code`
   - Password: Same as shop password
   - Role: `tenant_admin`
   - Linked to shop via `shop_id`

**Result**: Tenant admin can immediately login and start managing their shop.

## Example: Complete Workflow

### Step 1: Create Root Admin (Manual)
```bash
curl -X POST 'http://127.0.0.1:8000/users/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <root_admin_token>' \
  -d '{
    "username": "root_admin",
    "password": "root_password123",
    "role": "root_admin"
  }'
```

### Step 2: Root Admin Onboards a Shop
```bash
curl -X POST 'http://127.0.0.1:8000/shops/onboard' \
  -H 'Content-Type: application/json' \
  -d '{
    "shop": {
      "shop_name": "My Shop",
      "password": "shop_password123"
    },
    "owner": {
      "owner_name": "John Doe"
    }
  }'
```

**Response includes:**
- Shop details with `shop_code` (e.g., "MYSHOPA1B2")
- Tenant admin account created automatically

### Step 3: Tenant Admin Logs In
```bash
curl -X POST 'http://127.0.0.1:8000/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=MYSHOPA1B2&password=shop_password123'
```

### Step 4: Tenant Admin Creates Staff
```bash
curl -X POST 'http://127.0.0.1:8000/tenant/staff' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <tenant_admin_token>' \
  -d '{
    "username": "staff1",
    "password": "staff_password123",
    "role": "staff"
  }'
```

### Step 5: Tenant Admin or Staff Creates Customer
```bash
curl -X POST 'http://127.0.0.1:8000/customers/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <tenant_admin_or_staff_token>' \
  -d '{
    "customer_name": "Customer Name",
    "phone": "+919876543210",
    "email": "customer@example.com"
  }'
```

## Role Permissions Matrix

| Action | Root Admin | Tenant Admin | Staff | Customer |
|--------|-----------|--------------|-------|----------|
| Manage all shops | ✅ | ❌ | ❌ | ❌ |
| Manage own shop | ✅ | ✅ | ❌ | ❌ |
| Create tenant admin | ✅ | ❌ | ❌ | ❌ |
| Create staff | ✅ | ✅ | ❌ | ❌ |
| Create customer | ✅ | ✅ | ✅ | ❌ |
| View own shop data | ✅ | ✅ | ✅ | ✅ (own only) |
| Manage items/invoices | ✅ | ✅ | ✅ | ❌ |

## Security Notes

1. **Root Admin**: Should be created manually and protected
2. **Tenant Admin**: Created automatically during shop onboarding
3. **Staff**: Can only be created by tenant admin for their shop
4. **Customer**: Can be created by tenant admin or staff
5. **Role Validation**: All endpoints check user roles before allowing access
6. **Shop Isolation**: Users can only access resources from their linked shop

## Database Schema

### User Model
- `role`: `root_admin`, `tenant_admin`, `staff`, or `customer`
- `shop_id`: Links user to shop (NULL for root_admin)
- `is_active`: Account status

### Customer Model
- `shop_id`: Links customer to shop
- `customer_name`, `phone`, `email`, `address`
- `is_active`: Customer status

## Next Steps

1. Implement customer self-service endpoints
2. Add role-based filtering to existing endpoints (items, invoices, etc.)
3. Add audit logging for admin actions
4. Implement shop-level data isolation
