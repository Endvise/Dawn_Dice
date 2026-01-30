# DaWn Dice Party - Streamlit Cloud Deployment Guide

## Overview
This guide explains how to deploy the DaWn Dice Party application to Streamlit Cloud.

---

## Prerequisites

1. **GitHub Account** - Already created: `https://github.com/Endvise/Dawn_Dice`
2. **Streamlit Account** - Sign up at `https://streamlit.io/cloud`
3. **Python 3.11+** - Required for the application

---

## Deployment Steps

### 1. Configure Streamlit Secrets

**IMPORTANT:** Never commit `secrets.toml` to GitHub!

1. Copy the template:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

2. Edit `.streamlit/secrets.toml` with your values:
```toml
MASTER_USERNAME = "DaWnntt0623"
MASTER_PASSWORD = "4425endvise9897!"
DB_PATH = "data/dice_app.db"
PASSWORD_HASH_ROUNDS = 12
SESSION_TIMEOUT = 60
MAX_LOGIN_ATTEMPTS = 5
```

3. **DO NOT** commit `.streamlit/secrets.toml` to Git!

---

### 2. Connect Repository to Streamlit Cloud

1. Go to `https://streamlit.io/cloud`
2. Click "New app" or "+"
3. Select:
   - **Repository**: `Endvise/Dawn_Dice`
   - **Branch**: `master`
   - **Main file path**: `dice_app/app.py`

---

### 3. Configure Secrets in Streamlit Cloud

Instead of using `secrets.toml` locally, you need to configure secrets in Streamlit Cloud:

1. In your app settings, go to "Secrets"
2. Add the following secrets:

| Key | Value | Description |
|------|--------|-------------|
| `MASTER_USERNAME` | `DaWnntt0623` | Master admin username |
| `MASTER_PASSWORD` | `4425endvise9897!` | Master admin password |
| `DB_PATH` | `./data/dice_app.db` | Database path |
| `PASSWORD_HASH_ROUNDS` | `12` | Password hashing rounds |
| `SESSION_TIMEOUT` | `60` | Session timeout in minutes |
| `MAX_LOGIN_ATTEMPTS` | `5` | Max failed login attempts |

**Note:** `DB_PATH` should be `./data/dice_app.db` for Streamlit Cloud (uses `/mount/data/` internally).

---

### 4. Deploy

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
streamlit>=1.28.0
bcrypt>=4.0.0
openpyxl>=3.1.0
requests>=2.31.0
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

---

## Repository URLs

- **GitHub**: https://github.com/Endvise/Dawn_Dice
- **Streamlit Cloud**: https://share.streamlit.io/your-app-name

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
