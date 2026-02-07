#!/usr/bin/env python3
"""
User Guide Page - English
General user guide (English)
"""

import streamlit as st
import auth


def show():
    """Show user guide (English)"""
    auth.require_login()

    st.title("📖 How to Use")
    st.markdown("---")

    # Table of Contents (matching sidebar menu)
    st.markdown("""
    ## Table of Contents

    01. [Home](#01-home)
    02. [Make Reservation](#02-make-reservation)
    03. [My Reservations](#03-my-reservations)
    04. [ 이용 방법](#04---)
    05. [How to Use](#05-how-to-use)
    06. [Change Password](#06-change-password)
    """)

    st.markdown("---")

    # 01. Home
    st.markdown("## 01. Home")
    st.markdown("""
    **Menu Location:** Sidebar first

    **Description:**
    - Main page of the system
    - Shows current active session information
    - Displays reservation status (Open/Closed/Waitlist)
    - Check reservation open/close times

    **How to Use:**
    1. Select "01. 🏠 Home" from sidebar
    2. Check current session information
    3. Check reservation status
    """)

    st.markdown("---")

    # 02. Make Reservation
    st.markdown("## 02. Make Reservation")
    st.markdown("""
    **Menu Location:** Sidebar second

    **Description:**
    - Page to make a reservation
    - Only available during admin-set reservation times

    **How to Use:**
    1. Select "02. 📝 Make Reservation" from sidebar
    2. Enter Commander ID (10 digits)
    3. Check nickname, server, alliance info
    4. Submit reservation

    **Reservation Times:**
    - Check for **Reservations Open** status at the top
    - Opening time: Set by admin
    - Closing time: Set time OR when capacity is reached
    """)

    st.markdown("---")

    # 03. My Reservations
    st.markdown("## 03. My Reservations")
    st.markdown("""
    **Menu Location:** Sidebar third

    **Description:**
    - Shows reservation status for logged-in user
    - Check reservation order and status

    **How to Use:**
    1. Select "03. 📊 My Reservations" from sidebar
    2. Check your reservation list
    3. Check reservation order (Queue Position)
    - Within capacity: "You are #{order} in queue (within capacity)"
    - Waitlist: "You are #{order} in queue (waitlist #{waitlist#})"
    """)

    st.markdown("---")

    # 04. 이용 방법
    st.markdown("## 04. 이용 방법")
    st.markdown("""
    **Menu Location:** Sidebar fourth

    **Description:**
    - This guide page in Korean
    - System usage guide in Korean language

    **How to Use:**
    1. Select "04. 📖 이용 방법" from sidebar
    2. Read the guide in Korean
    """)

    st.markdown("---")

    # 05. How to Use
    st.markdown("## 05. How to Use")
    st.markdown("""
    **Menu Location:** Sidebar fifth

    **Description:**
    - This guide page in English
    - System usage guide in English language

    **How to Use:**
    1. Select "05. 📖 How to Use" from sidebar
    2. Read the guide in English
    """)

    st.markdown("---")

    # 06. Change Password
    st.markdown("## 06. Change Password")
    st.markdown("""
    **Menu Location:** Sidebar sixth

    **Description:**
    - Change your password

    **How to Use:**
    1. Select "06. 🔐 Change Password" from sidebar
    2. Enter current password
    3. Enter new password (minimum 8 characters)
    4. Confirm new password
    5. Click **Change Password** button

    **Forgot Your Password?**
    - **Contact the admin** to request a password reset
    - The admin will provide your new password
    """)

    st.markdown("---")

    # Important Notes
    st.markdown("## ⚠️ Important Notes")
    st.markdown("""
    ### First-Come, First-Served
    - Reservations are confirmed in order of application
    - When capacity (180) is exceeded, you will be automatically waitlisted

    ### Blacklist
    - Commander IDs on the blacklist cannot use this service
    - Contact admin for any inquiries

    ### Account Notes
    - Always change your password after a reset
    - Commander ID cannot be changed
    """)

    st.markdown("---")
