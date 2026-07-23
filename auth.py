import re
import smtplib
import random
import streamlit as st
from email.message import EmailMessage
import database as db
import time

OTP_TIMEOUT = 60

# Email Configuration
SENDER_EMAIL = "clarityhub2026@gmail.com"
SENDER_PASSWORD = "rwdc sdbj dqke qxet"  # Use Google App Password

def is_valid_email(email):
    if not email:
        return False
    pattern = r'^[A-Za-z0-9._%+-]*[A-Za-z]{3,}[A-Za-z0-9._%+-]*@gmail\.com$'
    return bool(re.match(pattern, email))


def is_valid_username(username):
    if not username or len(username) < 5:
        return False
    letters = re.findall(r'[A-Za-z]', username)
    has_number = bool(re.search(r'\d', username))
    return len(letters) >= 3 and has_number


def is_strong_password(password):
    if not password or len(password) < 6:
        return False
    return bool(re.search(r'[A-Za-z]', password) and re.search(r'\d', password))


def send_otp_email(receiver_email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your Clarity Hub verification code is: {otp}")
    msg['Subject'] = 'Clarity Hub - OTP Verification'
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        st.warning("📧 Email not configured - using test mode. OTP: " + otp)
        return True


def signup_interface():
    st.subheader("Create New Account")
    new_user = st.text_input("Username", key="reg_user")
    new_email = st.text_input("Email Address", key="reg_email")
    new_pass = st.text_input("Password", type='password', key="reg_pass")

    if st.button("Send OTP"):
        if not new_user or not new_email or not new_pass:
            st.warning("⚠️ Please fill all fields.")
            return

        if not is_valid_username(new_user):
            st.warning("⚠️ Username must be at least 5 characters, contain at least 3 letters, and include a number.")
            return

        if not is_valid_email(new_email):
            st.warning("⚠️ Email must be a valid Gmail address with at least 3 letters before @gmail.com.")
            return

        if not is_strong_password(new_pass):
            st.warning("⚠️ Password must be at least 6 characters long and contain both letters and numbers.")
            return

        otp = str(random.randint(100000, 999999))
        if db.add_pending_user(new_user, new_email, new_pass, otp):
            if send_otp_email(new_email, otp):
                st.success(f"✅ OTP sent to {new_email}")
                st.session_state.pending_user = new_user
                st.session_state.pending_email = new_email
                st.session_state.otp_sent_time = time.time()
            else:
                st.error("❌ Failed to send email. Check credentials.")
        else:
            st.error("❌ Username already taken.")

    if 'pending_user' in st.session_state:
        st.markdown("---")
        st.markdown("### 📧 OTP Verification")
        otp_input = st.text_input("Enter 6-digit OTP", key="otp_input_field")
        if 'otp_sent_time' in st.session_state:
            elapsed_time = time.time() - st.session_state.otp_sent_time
            remaining_time = max(0, int(OTP_TIMEOUT - elapsed_time))
            progress_value = 1 - (remaining_time / OTP_TIMEOUT)
            st.markdown(f"⏳ Time remaining to verify OTP: **{remaining_time} seconds**")
            st.progress(progress_value)

            if remaining_time <= 0:
                if st.button("🔄 Resend OTP", key="resend_otp_btn"):
                    otp = str(random.randint(100000, 999999))
                    if db.update_pending_user_otp(st.session_state.pending_user, otp):
                        if send_otp_email(st.session_state.pending_email, otp):
                            st.success(f"✅ New OTP sent to {st.session_state.pending_email}")
                            st.session_state.otp_sent_time = time.time()
                            st.rerun()
                        else:
                            st.error("❌ Failed to resend email.")
                    else:
                        st.error("❌ Failed to update OTP.")
            else:
                st.button("🔄 Resend OTP", key="resend_otp_disabled", disabled=True, help=f"Available after {remaining_time} seconds")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verify & Register", use_container_width=True):
                if otp_input:
                    if db.verify_otp_in_db(st.session_state.pending_user, otp_input):
                        st.success("🎉 Registration Successful! You are now logged in.")
                        st.session_state.logged_in = True
                        st.session_state.username = st.session_state.pending_user
                        st.session_state.role = 'user'
                        st.session_state.nav_choice = 'AI Chatbot'
                        db.save_activity_log(st.session_state.username, 'Login', 'User auto-logged in after registration')
                        del st.session_state.pending_user
                        del st.session_state.pending_email
                        if 'otp_sent_time' in st.session_state:
                            del st.session_state.otp_sent_time
                        st.experimental_rerun()
                    else:
                        st.error("❌ Invalid OTP code.")
                else:
                    st.warning("⚠️ Please enter the OTP.")

        with col2:
            if st.button("← Back to Registration", use_container_width=True):
                del st.session_state.pending_user
                del st.session_state.pending_email
                if 'otp_sent_time' in st.session_state:
                    del st.session_state.otp_sent_time
                st.rerun()