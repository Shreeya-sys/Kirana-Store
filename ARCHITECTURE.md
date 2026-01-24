# KiranaFlow - Architecture & Implementation Guide

**Version**: 1.0
**Date**: January 24, 2026
**Internal Codename**: KiranaFlow

---

## 1. Executive Summary
**KiranaFlow** is a multi-tenant, offline-first accounting platform designed for Indian SMBs (Kirana stores). It addresses "Invisible Loss" through granular inventory tracking (Break-Bulk) and simplifies credit (Udhaar) management.

## 2. Technical Architecture

### 2.1 Technology Stack
- **Frontend**: Flutter (Windows, Android, Web). *Currently in `frontend/` (Manual Generation).*
- **Backend**: Python FastAPI.
- **Database**:
    - **Production**: PostgreSQL (Planned).
    - **Development/Local**: SQLite (`kiranaflow.db`).
- **ORM**: SQLAlchemy.
- **Authentication**: JWT (JSON Web Tokens) with Role-Based Access Control (RBAC).

### 2.2 System Diagram
```mermaid
graph TD
    Client[Flutter Client (Mobile/Desktop)] -->|REST API / JSON| API[FastAPI Backend]
    API -->|SQLAlchemy| DB[(SQLite/Postgres)]
    
    subgraph "Core Modules"
    API --> Auth[Auth Module]
    API --> Inv[Hyper-Inventory Engine]
    API --> POS[POS & Billing]
    API --> Compliance[GST & Audit]
    end
    
    subgraph "Data Flow"
    Inv -->|Decant| DB
    POS -->|Invoice| DB
    POS -->|Update| Ledger[Credit Ledger]
    end
```

## 3. Database Schema

### 3.1 User Management (`users`)
- `id`: Integer (PK)
- `username`: String (Unique)
- `role`: String (`admin`, `staff`)
- `tenant_id`: String (Multi-tenancy)

### 3.2 Hyper-Inventory (`items`, `stock_adjustments`)
Supports **Dual-Unit Tracking** to solve spillage.
- **Item**:
    - `parent_unit`: e.g., "Sack"
    - `child_unit`: e.g., "Gram"
    - `conversion_factor`: e.g., 10,000 (1 Sack = 10,000 Grams)
    - `bulk_qty`: Stock in Parent Units.
    - `loose_qty`: Stock in Child Units.
- **StockAdjustment**:
    - Logs every movement: `DECANT`, `SALE`, `PURCHASE`.
    - Tracks `quantity_change_bulk` and `quantity_change_loose`.

### 3.3 POS & Credit (`invoices`, `invoice_items`, `ledgers`)
- **Invoice**:
    - `customer_phone`: Link to Ledger.
    - `status`: `PAID` or `CREDIT`.
- **Ledger**:
    - Tracks `debit_amount` (Udhaar given) and `credit_amount` (Payment received).
    - `balance`: Net outstanding.

### 3.4 Compliance (`audit_logs`)
- MCA Mandate: Immutable logs for `CREATE`, `UPDATE`, `DELETE` actions on critical tables.

## 4. API Endpoints

### Authentication
- `POST /token`: Login & Get JWT.
- `GET /users/me`: Get current user profile.
- `POST /users/`: Register new user.

### Inventory
- `POST /items/`: Create new Product.
- `POST /inventory/decant/{id}`: Convert 1 Bulk Unit -> Loose Units.

### POS & Billing
- `POST /invoices/`: Generate Bill.
    - Automatic Stock Deduction.
    - Automatic Ledger Entry (if Status = CREDIT).
- `GET /ledger/{phone}`: Get Customer Credit History.

## 5. Implementation Details

### 5.1 The "Decant" Logic
The core innovation for solving "Invisible Loss".
1.  **Trigger**: User opens a new Sack.
2.  **Action**: `bulk_qty` -= 1.
3.  **Result**: `loose_qty` += `conversion_factor`.
4.  **Audit**: A generic mechanism tracks this conversion to prevent theft.

### 5.2 Offline-First Strategy (Planned)
- Currently using SQLite for local persistence.
- Future state: Drift (Flutter) <-> Sync Engine <-> PostgreSQL (Cloud).

### 5.3 GST Engine (`gst_engine.py`)
- Python utility to calculate Taxable Value, CGST, and SGST based on HSN codes.
- Default Logic: Intra-state (CGST+SGST) split.

## 6. Project Structure
```
root/
├── backend/
│   ├── main.py           # API Entry Point
│   ├── models.py         # DB Models
│   ├── schemas.py        # Pydantic Schemas
│   ├── crud.py           # DB Logic
│   ├── auth.py           # JWT Security
│   ├── gst_engine.py     # Tax Logic
│   └── test_*.py         # Unit Tests
├── frontend/
│   ├── lib/
│   │   ├── core/         # API Client
│   │   ├── features/
│   │   │   ├── auth/     # Login UI
│   │   │   └── dashboard/# Main UI
│   │   └── main.dart     # App Entry
└── requirements.txt      # Python Deps
```

## 7. Next Steps
1.  **Frontend Integration**: Connect the generated Flutter screens to the Backend API.
2.  **Hardware Stub**: Create a mock service for Bluetooth Scale integration.
3.  **Sync Engine**: Implement `last_updated_at` delta sync.
