# KiranaFlow

**Internal Codename**: KiranaFlow
**Version**: 1.0
**Target Market**: Indian SMBs (Kirana, General Stores, Wholesalers)

## Problem & Solution
Solving "Invisible Loss" in Kirana stores with a multi-tenant, offline-first accounting platform.
Prioritizes Store Automation (Scales, Voice) over manual entry.

## Tech Stack
- **Frontend**: Flutter (Mobile, Web, Desktop)
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL (Production) / SQLite (Local/Dev)
- **Auth**: JWT with RBAC

## Setup
### Backend
1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run server: `uvicorn main:app --reload`

### Frontend
1. Navigate to `frontend/`
2. Run: `flutter run`
