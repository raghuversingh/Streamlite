import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import database as db
import ml_agent


def admin_panel():
    st.header("👑 Admin Control Panel")

    if 'role' not in st.session_state or st.session_state.role != 'admin':
        st.error("Admin access only. Please login with an admin account.")
        return

    if 'admin_page' not in st.session_state:
        st.session_state.admin_page = 'Manage Accounts'

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("👥 Manage User Accounts", use_container_width=True):
            st.session_state.admin_page = 'Manage Accounts'
    with col2:
        if st.button("📊 Track User Mood & Feedback", use_container_width=True):
            st.session_state.admin_page = 'Track Mood'
    with col3:
        if st.button("📈 Analytics Dashboard", use_container_width=True):
            st.session_state.admin_page = 'Analytics Dashboard'
    with col4:
        if st.button("📝 User Activity Logs", use_container_width=True):
            st.session_state.admin_page = 'Activity Logs'
    with col5:
        if st.button("🕒 Admin History", use_container_width=True):
            st.session_state.admin_page = 'Admin History'

    st.markdown("---")

    conn = sqlite3.connect('clarity_hub.db')

    if st.session_state.admin_page == 'Manage Accounts':
        users_df = pd.read_sql_query("SELECT username, email, role, is_verified FROM users", conn)
        admins_df = pd.read_sql_query("SELECT username, email, is_active FROM admins", conn)

        st.subheader("📋 Registered Users")
        st.dataframe(users_df)

        st.markdown("---")
        st.subheader("👑 Admin Accounts")
        st.dataframe(admins_df)

        st.markdown("---")
        st.subheader("Manage User Accounts")
        if users_df.empty:
            st.info("No registered users available to manage.")
        else:
            selected_user = st.selectbox("User", users_df['username'].tolist(), key='admin_user_select')
            selected_action = st.radio("Action", ["Promote to Admin", "Delete User"], index=0)

            if st.button("Apply", key='admin_apply_action'):
                if selected_user == 'admin':
                    st.warning("Default admin account cannot be deleted or promoted.")
                else:
                    if selected_action == "Delete User":
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (selected_user,))
                        conn.commit()
                        st.success(f"User {selected_user} deleted.")
                        db.log_admin_action(st.session_state.username, 'Delete User', f'Deleted user {selected_user}')
                    elif selected_action == "Promote to Admin":
                        c = conn.cursor()
                        c.execute("SELECT email, password FROM users WHERE username=?", (selected_user,))
                        user_data = c.fetchone()
                        if user_data:
                            email, password_hash = user_data
                            success = db.add_admin_account(selected_user, email, password_hash, is_hashed=True)
                            if success:
                                c.execute("DELETE FROM users WHERE username=?", (selected_user,))
                                conn.commit()
                                st.success(f"User {selected_user} promoted to admin.")
                                db.log_admin_action(st.session_state.username, 'Promote to Admin', f'Promoted {selected_user} to admin')
                            else:
                                st.error("Failed to promote user. Admin username may already exist.")
                        else:
                            st.error("Selected user data could not be loaded.")

                    users_df = pd.read_sql_query("SELECT username, email, role, is_verified FROM users", conn)
                    admins_df = pd.read_sql_query("SELECT username, email, is_active FROM admins", conn)
                    st.dataframe(users_df)
                    st.dataframe(admins_df)

    elif st.session_state.admin_page == 'Track Mood':
        users_df = pd.read_sql_query("SELECT username FROM users", conn)
        st.subheader("Track User Mood & Feedback")

        if users_df.empty:
            st.info("No users available to track.")
        else:
            track_user = st.selectbox("Select User to Track", users_df['username'].tolist(), key='track_user_select')
            if st.button("View Mood & Feedback", key='view_mood_feedback'):
                mood_df = pd.read_sql_query("SELECT date, score FROM mood_logs WHERE username=?", conn, params=(track_user,))
                if not mood_df.empty:
                    st.write(f"**Mood Progress for {track_user}**")
                    fig = px.line(mood_df, x='date', y='score', markers=True, 
                                 labels={"score": "Mood Level (1-5)", "date": "Day"},
                                 color_discrete_sequence=['#2E7D32'])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No mood data for {track_user}.")

                journal_df = db.get_user_journals(track_user)
                if not journal_df.empty:
                    st.write(f"**Journal Feedback for {track_user}**")
                    for _, row in journal_df.iterrows():
                        st.markdown(f"**{row['date_time']}**: {row['entry_text']}")
                else:
                    st.info(f"No journal entries for {track_user}.")

                db.log_admin_action(st.session_state.username, 'View Mood & Feedback', f'Viewed mood and journal for {track_user}')

    elif st.session_state.admin_page == 'Analytics Dashboard':
        st.subheader("📈 Analytics Dashboard")
        users_df = pd.read_sql_query("SELECT username FROM users WHERE is_verified=1", conn)
        admin_df = pd.read_sql_query("SELECT username FROM admins WHERE is_active=1", conn)
        mood_df = pd.read_sql_query("SELECT username, score FROM mood_logs", conn)
        journal_df = pd.read_sql_query("SELECT username, date_time FROM journals", conn)
        activity_df = pd.read_sql_query("SELECT username, activity_type FROM activity_logs", conn)
        chat_df = pd.read_sql_query("SELECT username FROM chat_history", conn)

        total_users = len(users_df)
        total_admins = len(admin_df)
        total_journal_entries = len(journal_df)
        total_chat_entries = len(chat_df)
        total_activity_events = len(activity_df)
        avg_mood = float(mood_df['score'].mean()) if not mood_df.empty else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Verified Users", total_users)
        col2.metric("Active Admins", total_admins)
        col3.metric("Average Mood Score", f"{avg_mood:.2f}")
        col4.metric("Activity Events", total_activity_events)

        if not mood_df.empty or not activity_df.empty:
            charts = st.columns(2)
            if not mood_df.empty:
                mood_summary = mood_df.groupby('username', as_index=False)['score'].mean().sort_values('score', ascending=False)
                fig1 = px.bar(mood_summary.head(10), x='username', y='score', title='Average Mood Score by User', color='score', color_continuous_scale='Viridis')
                charts[0].plotly_chart(fig1, use_container_width=True)
            if not activity_df.empty:
                activity_count = activity_df['username'].value_counts().reset_index()
                activity_count.columns = ['username', 'activity_count']
                fig2 = px.bar(activity_count.head(10), x='username', y='activity_count', title='Top Active Users', color='activity_count', color_continuous_scale='Turbo')
                charts[1].plotly_chart(fig2, use_container_width=True)

        if not users_df.empty:
            risk_levels = []
            for username in users_df['username'].tolist():
                risk = ml_agent.ml_agent.detect_risk(username)
                risk_levels.append({'username': username, 'risk_level': risk['level']})
            risk_df = pd.DataFrame(risk_levels)
            risk_counts = risk_df['risk_level'].value_counts().reset_index()
            risk_counts.columns = ['risk_level', 'count']
            fig3 = px.pie(risk_counts, names='risk_level', values='count', title='Risk Distribution Across Users')
            st.plotly_chart(fig3, use_container_width=True)

    elif st.session_state.admin_page == 'Activity Logs':
        st.subheader("📝 User Activity Logs")
        users_df = pd.read_sql_query("SELECT username FROM users", conn)
        if users_df.empty:
            st.info("No users available.")
        else:
            selected_user = st.selectbox("Select User", users_df['username'].tolist(), key='activity_user_select')
            if st.button("Load Activity Logs", key='load_activity_logs'):
                activity_df = db.get_user_activity_logs(selected_user)
                if not activity_df.empty:
                    st.dataframe(activity_df)
                else:
                    st.info(f"No activity logs for {selected_user}.")
                db.log_admin_action(st.session_state.username, 'View Activity Logs', f'Viewed activity logs for {selected_user}')

    elif st.session_state.admin_page == 'Admin History':
        st.subheader("🕒 Admin Action History")
        history_df = db.get_admin_history()
        if history_df.empty:
            st.info("No admin actions recorded yet.")
        else:
            st.dataframe(history_df)

    conn.close()