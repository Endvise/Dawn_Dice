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

    # Table of Contents
    st.markdown("""
    ## Table of Contents
    
    1. [Registration](#registration)
    2. [Login](#login)
    3. [Making a Reservation](#making-a-reservation)
    4. [My Reservations](#my-reservations)
    5. [Changing Password](#changing-password)
    6. [Important Notes](#important-notes)
    """)

    st.markdown("---")

    # 1. Registration
    st.markdown("## 1. Registration")
    st.markdown("""
    1. Click **Sign Up** button on the login page
    2. Enter the following information:
       - **Commander ID**: 10-digit number (e.g., 1234567890)
       - **Nickname**: Your desired nickname
       - **Server**: Server number (e.g., #095)
       - **Alliance**: Alliance name (optional)
       - **Password**: Minimum 8 characters
    3. Click **Sign Up** button
    """)

    st.markdown("---")

    # 2. Login
    st.markdown("## 2. Login")
    st.markdown("""
    1. Enter your Commander ID (or username) and password
    2. Click **Login** button

    ### Forgot Your Password?
    - **Contact the admin** to request a password reset
    - The admin will provide your new password
    """)

    st.markdown("---")

    # 3. Making a Reservation
    st.markdown("## 3. Making a Reservation")
    st.markdown("""
    1. Click **Go to Reservation** button when reservations are open
    2. Review your information
    3. Click **Submit** button
    4. Your reservation is confirmed!

    ### Reservation Times
    - Check for **Reservations Open** status at the top
    - Opening time: Set by admin
    - Closing time: Set time OR when capacity is reached
    """)

    st.markdown("---")

    # 4. My Reservations
    st.markdown("## 4. My Reservations")
    st.markdown("""
    - Check your reservation status in **My Reservations** menu
    - View your reservation number (queue position)
    - If waitlisted, see your waitlist number
    """)

    st.markdown("---")

    # 5. Changing Password
    st.markdown("## 5. Changing Password")
    st.markdown("""
    1. Go to **Change Password** menu
    2. Enter your current password
    3. Enter new password (minimum 8 characters)
    4. Confirm new password
    5. Click **Change Password** button
    """)

    st.markdown("---")

    # 6. Important Notes
    st.markdown("## 6. Important Notes")
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
