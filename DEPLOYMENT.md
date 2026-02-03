# DaWn Dice Party - Streamlit Cloud Deployment Guide

## Overview
This guide explains how to deploy the DaWn Dice Party application to Streamlit Cloud.

---

## Prerequisites

1. **GitHub Account** - Already created: `https://github.com/Endvise/Dawn_Dice`
2. **Streamlit Account** - Sign up at `https://streamlit.io/cloud`
3. **Python 3.11+** - Required for the application
4. **Supabase Account** (Optional) - For persistent database storage

---

## Deployment Steps

### 1. Choose Database Type

#### Option A: Supabase/PostgreSQL (Recommended for production)
**Pros**: Data persists across deployments, professional-grade database
**Cons**: Requires Supabase account

#### Option B: SQLite (Default - ephemeral on Streamlit Cloud)
**Pros**: No additional setup
**Cons**: Data resets on every deployment

---

### 2. Configure Streamlit Secrets

**IMPORTANT:** Never commit `secrets.toml` to GitHub!

#### For Supabase/PostgreSQL:
1. Copy the template:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

2. Edit `.streamlit/secrets.toml` with your Supabase values:
```toml
MASTER_USERNAME = "DaWnntt0623"
MASTER_PASSWORD = "your_secure_password"

# PostgreSQL (Supabase)
DB_TYPE = "postgresql"
DB_CONNECTION_STRING = "postgresql://postgres:password@db.project.supabase.co:5432/postgres"

PASSWORD_HASH_ROUNDS = 12
SESSION_TIMEOUT = 60
MAX_LOGIN_ATTEMPTS = 5
```

#### For SQLite (local development only):
```toml
DB_TYPE = "sqlite"
DB_PATH = "./data/dice_app.db"
```

3. **DO NOT** commit `.streamlit/secrets.toml` to Git!

---

### 3. Supabase Setup (Optional but Recommended)

#### Create Supabase Project
1. Go to https://supabase.com and sign up
2. Create a new project
3. Note your project credentials

#### Get Connection String
1. Go to Project Settings → Database
2. Find "Connection string" (URI)
3. Copy the format: `postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres`

#### Create Tables
The app will auto-create tables on first run. For manual setup, run:
```sql
-- Users 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    commander_id TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    nickname TEXT,
    server TEXT,
    alliance TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0
);

-- Reservations 테이블
CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    nickname TEXT NOT NULL,
    commander_id TEXT NOT NULL,
    server TEXT NOT NULL,
    alliance TEXT,
    status TEXT DEFAULT 'pending',
    is_blacklisted INTEGER DEFAULT 0,
    blacklist_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER,
    notes TEXT,
    waitlist_order INTEGER,
    waitlist_position INTEGER
);

-- Blacklist 테이블
CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    commander_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    reason TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,
    is_active INTEGER DEFAULT 1
);

-- Participants 테이블
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    number INTEGER,
    nickname TEXT,
    affiliation TEXT,
    igg_id TEXT,
    alliance TEXT,
    wait_confirmed INTEGER DEFAULT 0,
    confirmed INTEGER DEFAULT 0,
    notes TEXT,
    completed INTEGER DEFAULT 0,
    participation_record TEXT,
    event_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Announcements 테이블
CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'notice',
    is_pinned INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Event Sessions 테이블
CREATE TABLE IF NOT EXISTS event_sessions (
    id SERIAL PRIMARY KEY,
    session_number INTEGER,
    session_name TEXT,
    session_date DATE,
    max_participants INTEGER DEFAULT 180,
    reservation_open_time DATETIME,
    reservation_close_time DATETIME,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Servers 테이블
CREATE TABLE IF NOT EXISTS servers (
    id SERIAL PRIMARY KEY,
    server_name TEXT UNIQUE NOT NULL,
    server_code TEXT UNIQUE,
    is_active INTEGER DEFAULT 1
);

-- Alliances 테이블
CREATE TABLE IF NOT EXISTS alliances (
    id SERIAL PRIMARY KEY,
    alliance_name TEXT UNIQUE NOT NULL,
    server_id INTEGER,
    is_active INTEGER DEFAULT 1
);
```

---

### 4. Connect Repository to Streamlit Cloud

1. Go to `https://streamlit.io/cloud`
2. Click "New app" or "+"
3. Select:
   - **Repository**: `Endvise/Dawn_Dice`
   - **Branch**: `master`
   - **Main file path**: `dice_app/app.py`

---

### 5. Configure Secrets in Streamlit Cloud

#### For Supabase/PostgreSQL:
Add these secrets in Streamlit Cloud settings:

| Key | Value | Description |
|------|--------|-------------|
| `MASTER_USERNAME` | `DaWnntt0623` | Master admin username |
| `MASTER_PASSWORD` | `your_password` | Master admin password |
| `DB_TYPE` | `postgresql` | Database type |
| `DB_CONNECTION_STRING` | `postgresql://...` | Supabase connection string |
| `PASSWORD_HASH_ROUNDS` | `12` | Password hashing rounds |
| `SESSION_TIMEOUT` | `60` | Session timeout in minutes |
| `MAX_LOGIN_ATTEMPTS` | `5` | Max failed login attempts |

#### For SQLite (not recommended for production):
| Key | Value | Description |
|------|--------|-------------|
| `DB_TYPE` | `sqlite` | Database type |
| `DB_PATH` | `./data/dice_app.db` | Database path |

---

### 6. Deploy

1. Click "Deploy" in Streamlit Cloud
2. Wait for deployment to complete (usually 1-2 minutes)
3. Your app will be available at: `https://your-app-name.streamlit.app`

---

## Post-Deployment Checklist

### Test Master Account
- [ ] Log in with master credentials
- [ ] Create admin accounts
- [ ] Verify dashboard works

### Test User Flow
- [ ] User registration (10-digit commander ID)
- [ ] User login
- [ ] Make reservation
- [ ] Check waitlist when full

### Test Admin Flow
- [ ] Approve/reject reservations
- [ ] Add to blacklist
- [ ] Post announcements
- [ ] Create event sessions
- [ ] Import Excel participant list

### Security Verification
- [ ] F12 dev tools blocked for users
- [ ] 5 failed login attempts lock account
- [ ] Session timeout works (60 min)
- [ ] Blacklist blocks registration

---

## Troubleshooting

### Issue: Database errors on first run
**Solution:** The app will auto-create the database on first run. Just wait a few seconds.

### Issue: "Module not found" errors
**Solution:** Check `requirements.txt` is in the repository root:
```
streamlit>=1.41.0
bcrypt>=4.2.1
openpyxl>=3.1.5
requests>=2.32.5
markdown>=3.7
pillow>=11.3.0
python-docx>=1.2.0
psycopg2-binary>=2.9.10
```

### Issue: Secrets not working
**Solution:**
1. Verify secrets are set in Streamlit Cloud (not local)
2. Key names must match exactly (case-sensitive)
3. Click "Redeploy" after changing secrets

### Issue: Google Sheets blacklist not working
**Solution:** Add `BLACKLIST_GOOGLE_SHEET_URL` to secrets:
```toml
BLACKLIST_GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/..."
```

### Issue: Data disappears after redeployment (SQLite only)
**Solution:** Switch to Supabase/PostgreSQL as documented above. SQLite data is ephemeral on Streamlit Cloud.

---

## Repository URLs

- **GitHub**: https://github.com/Endvise/Dawn_Dice
- **Streamlit Cloud**: https://share.streamlit.io/your-app-name
- **Supabase**: https://supabase.com

---

## Application Features

- ✅ User registration (10-digit commander ID)
- ✅ Login system with bcrypt hashing
- ✅ Reservation application with priority queue
- ✅ Session-based event management
- ✅ Waitlist system (FIFO)
- ✅ Admin dashboard with real-time stats
- ✅ Blacklist management (local + Google Sheets)
- ✅ Announcements (Markdown support)
- ✅ Participant management with Excel import
- ✅ Security features (F12 blocking, login limits, session timeout)
- ✅ PostgreSQL/Supabase support for persistent data

---

## Default Master Account

| Username | Password |
|----------|----------|
| `DaWnntt0623` | `4425endvise9897!` |

**⚠️ Security Warning:** Change this password after first login in production!

---

## Support

For issues or questions:
1. Check GitHub Issues: `https://github.com/Endvise/Dawn_Dice/issues`
2. Review code in: `https://github.com/Endvise/Dawn_Dice`

---

## Deployment Success!

Your DaWn Dice Party app is now deployed and ready for use!
