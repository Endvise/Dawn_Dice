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

#### For Supabase (REST API - Recommended):
**Pros**: Simple HTTP API, no driver issues, works well with Streamlit Cloud
**Cons**: Requires Supabase account

#### Get Supabase Credentials:
1. Go to https://supabase.com and sign up
2. Create a new project
3. Go to Project Settings → API
4. Copy:
   - **URL**: `https://your-project.supabase.co`
   - **anon key**: `eyJ...` (public key, safe to expose)

#### Create Tables in Supabase Dashboard:
1. Go to Table Editor in Supabase dashboard
2. Create the following tables:

**users table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key, auto-generated |
| username | text | Unique |
| commander_id | text | Unique |
| password_hash | text | |
| role | text | Default: 'user' |
| nickname | text | |
| server | text | |
| alliance | text | |
| is_active | int4 | Default: 1 |
| created_at | timestamptz | Default: now() |
| last_login | timestamptz | |
| failed_attempts | int4 | Default: 0 |

**reservations table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| user_id | int4 | |
| nickname | text | |
| commander_id | text | |
| server | text | |
| alliance | text | |
| status | text | Default: 'pending' |
| is_blacklisted | int4 | Default: 0 |
| blacklist_reason | text | |
| created_at | timestamptz | Default: now() |
| approved_at | timestamptz | |
| approved_by | int4 | |
| notes | text | |
| waitlist_order | int4 | |
| waitlist_position | int4 | |

**blacklist table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| commander_id | text | Unique |
| nickname | text | |
| reason | text | |
| added_at | timestamptz | Default: now() |
| added_by | int4 | |
| is_active | int4 | Default: 1 |

**participants table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| number | int4 | |
| nickname | text | |
| affiliation | text | |
| igg_id | text | |
| alliance | text | |
| wait_confirmed | int4 | Default: 0 |
| confirmed | int4 | Default: 0 |
| notes | text | |
| completed | int4 | Default: 0 |
| participation_record | text | |
| event_name | text | |
| created_at | timestamptz | Default: now() |

**announcements table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| title | text | |
| content | text | |
| category | text | Default: 'notice' |
| is_pinned | int4 | Default: 0 |
| created_by | int4 | |
| created_at | timestamptz | Default: now() |
| updated_at | timestamptz | |
| is_active | int4 | Default: 1 |

**event_sessions table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| session_number | int4 | |
| session_name | text | |
| session_date | date | |
| max_participants | int4 | Default: 180 |
| reservation_open_time | timestamptz | |
| reservation_close_time | timestamptz | |
| is_active | int4 | Default: 1 |
| created_by | int4 | |
| created_at | timestamptz | Default: now() |

**servers table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| server_name | text | Unique |
| server_code | text | Unique |
| is_active | int4 | Default: 1 |

**alliances table:**
| Column | Type | Notes |
|--------|------|-------|
| id | int8 | Primary key |
| alliance_name | text | Unique |
| server_id | int4 | |
| is_active | int4 | Default: 1 |

Enable RLS (Row Level Security) on all tables for security.

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

#### For Supabase (REST API):
Add these secrets in Streamlit Cloud settings:

| Key | Value | Description |
|------|--------|-------------|
| `MASTER_USERNAME` | `DaWnntt0623` | Master admin username |
| `MASTER_PASSWORD` | `your_password` | Master admin password |
| `DB_TYPE` | `supabase` | Database type |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Supabase project URL |
| `SUPABASE_KEY` | `your_anon_key` | Supabase anon key (from Project Settings → API) |
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
