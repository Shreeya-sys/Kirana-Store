# KiranaFlow - Step-by-Step Run Instructions

## Prerequisites

### Backend Prerequisites
- ✅ Python 3.7+ installed
- ✅ pip (Python package manager)

### Frontend Prerequisites
- ✅ Flutter SDK installed
- ✅ Flutter in PATH (verify with `flutter --version`)
- ✅ For Windows: Visual Studio with C++ build tools (for native compilation)

---

## Step 1: Backend Setup

### 1.1 Navigate to Backend Directory
```bash
cd backend
```

### 1.2 Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Expected output**: All packages should install successfully:
- fastapi
- uvicorn
- sqlalchemy
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart

### 1.3 Verify Database File
The database file `kiranaflow.db` will be created automatically when you start the server.

**Note**: If you're in OneDrive folder and get I/O errors:
- Option A: Move project outside OneDrive
- Option B: Pause OneDrive sync temporarily
- Option C: Change database path in `database.py` to a local folder

### 1.4 Start the Backend Server
```bash
uvicorn main:app --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 1.5 Verify Backend is Running
Open your browser and visit:
- **API Root**: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

You should see the API documentation.

**Keep this terminal window open** - the server needs to keep running.

---

## Step 2: Frontend Setup

### 2.1 Open a NEW Terminal Window
Keep the backend server running in the first terminal, open a new one for frontend.

### 2.2 Navigate to Frontend Directory
```bash
cd frontend
```

### 2.3 Install Flutter Dependencies
```bash
flutter pub get
```

**Expected output**: Should download and install:
- dio: ^5.3.3
- flutter_riverpod: ^2.4.4
- shared_preferences: ^2.2.1

### 2.4 Verify Flutter Setup
```bash
flutter doctor
```

This checks your Flutter installation. Fix any issues it reports.

### 2.5 Run the Flutter App

**For Windows Desktop:**
```bash
flutter run -d windows
```

**For Web:**
```bash
flutter run -d chrome
```

**For Android (if emulator/device connected):**
```bash
flutter run -d android
```

**To see available devices:**
```bash
flutter devices
```

### 2.6 First Run Notes
- First run may take longer (compiling)
- The app will open automatically
- Default backend URL is `http://127.0.0.1:8000`

---

## Step 3: Testing the Application

### 3.1 Create a Test User (via API)

**Option A: Using Swagger UI**
1. Go to http://127.0.0.1:8000/docs
2. Find `POST /users/` endpoint
3. Click "Try it out"
4. Enter:
```json
{
  "username": "admin",
  "password": "admin123",
  "role": "admin"
}
```
5. Click "Execute"

**Option B: Using curl**
```bash
curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\",\"role\":\"admin\"}"
```

### 3.2 Login via Flutter App
1. Open the Flutter app
2. Enter username: `admin`
3. Enter password: `admin123`
4. Click "LOGIN"
5. You should be redirected to the Dashboard

---

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
- **Solution**: Run `pip install -r requirements.txt` again

**Problem**: `sqlite3.OperationalError: disk I/O error`
- **Solution**: 
  - Move project outside OneDrive folder, OR
  - Pause OneDrive sync, OR
  - Change database path in `backend/database.py`:
    ```python
    SQLALCHEMY_DATABASE_URL = "sqlite:///C:/temp/kiranaflow.db"
    ```

**Problem**: Port 8000 already in use
- **Solution**: Use a different port:
  ```bash
  uvicorn main:app --reload --port 8001
  ```
  Then update `frontend/lib/core/api_client.dart` baseUrl to `http://127.0.0.1:8001`

### Frontend Issues

**Problem**: `flutter: command not found`
- **Solution**: 
  - Install Flutter SDK from https://flutter.dev
  - Add Flutter to PATH
  - Restart terminal

**Problem**: `Waiting for another flutter command to release the startup lock`
- **Solution**: 
  - Close other Flutter processes
  - Delete `flutter_tools.stamp` in Flutter SDK if needed

**Problem**: Cannot connect to backend
- **Solution**: 
  - Verify backend is running on http://127.0.0.1:8000
  - For Android emulator, change baseUrl to `http://10.0.2.2:8000` in `api_client.dart`
  - Check firewall isn't blocking connections

**Problem**: `dio` package not found
- **Solution**: Run `flutter pub get` in the frontend directory

---

## Quick Start Commands Summary

### Terminal 1 (Backend):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Terminal 2 (Frontend):
```bash
cd frontend
flutter pub get
flutter run -d windows
```

---

## Development Workflow

1. **Start Backend First**: Always start the backend server before the frontend
2. **Keep Backend Running**: Don't close the backend terminal while developing
3. **Hot Reload**: 
   - Backend: Auto-reloads on file changes (thanks to `--reload`)
   - Frontend: Press `r` in Flutter terminal for hot reload, `R` for hot restart
4. **Stop Servers**: Press `CTRL+C` in respective terminals

---

## Next Steps After Running

1. **Create Test Data**: Use Swagger UI to create items, invoices
2. **Test Features**: 
   - Login/Logout
   - Create items
   - Decant inventory
   - Create invoices
   - View ledger
3. **Explore API**: Visit http://127.0.0.1:8000/docs for full API documentation

---

## Support

If you encounter issues not covered here:
1. Check `SETUP_VERIFICATION.md` for architecture details
2. Review error messages carefully
3. Verify all prerequisites are installed
4. Check that ports are not in use by other applications
