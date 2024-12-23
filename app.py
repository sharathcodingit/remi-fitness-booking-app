```python
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from git import Repo
import traceback

# Constants
FILE_NAME = "clients.csv"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

def sync_with_github(commit_message="Updated client data"):
    """Function to sync changes with GitHub"""
    try:
        repo = Repo(REPO_PATH)
        
        # Add changes
        repo.git.add('clients.csv')
        
        # Only commit if there are changes
        if repo.is_dirty() or len(repo.untracked_files) > 0:
            repo.index.commit(commit_message)
            
            # Configure git with token authentication
            if 'SECRET_TOKEN' in st.secrets:
                token = st.secrets['SECRET_TOKEN']
                repo_url = repo.remotes.origin.url
                if repo_url.startswith('https://'):
                    new_url = f'https://x-access-token:{token}@github.com/sharathcodingit/remi-fitness-booking-app.git'
                    repo.remotes.origin.set_url(new_url)
            
            # Pull before pushing to avoid conflicts
            repo.git.pull('origin', 'main', '--no-rebase')
            
            # Push changes
            origin = repo.remote('origin')
            origin.push()
            
            print("GitHub sync completed successfully")
            return True
        return True
    except Exception as e:
        print(f"GitHub sync error: {str(e)}")
        print(traceback.format_exc())
        return False

def load_clients_from_csv(file_name=FILE_NAME):
    """Function to load client data from CSV"""
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            # Convert 'booked_sessions' from string to list
            df["booked_sessions"] = df["booked_sessions"].apply(
                lambda x: eval(x) if pd.notna(x) and x != '[]' else []
            )
            return df.to_dict(orient="index")
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
    return {}

def save_clients_to_csv(clients, file_name=FILE_NAME):
    """Function to save client data to CSV and sync with GitHub"""
    try:
        # Create a copy of the clients dictionary
        clients_copy = {}
        for name, data in clients.items():
            clients_copy[name] = data.copy()
            clients_copy[name]['booked_sessions'] = str(data['booked_sessions'])
        
        # Create DataFrame and save
        df = pd.DataFrame.from_dict(clients_copy, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'client_name'}, inplace=True)
        df.to_csv(file_name, index=False)
        
        # Sync with GitHub
        if sync_with_github():
            st.success("Changes saved and synced successfully!")
        else:
            st.warning("Changes saved locally but GitHub sync failed.")
            
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        print(f"Error details: {str(e)}")

# Initialize clients in session state
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_from_csv()

# App title
st.title("Fitness Trainer App")

# Introduction
st.write("Welcome! Use this app to manage client sessions, bookings, and payments.")

# Client Onboarding Section
st.header("Add a New Client")

with st.form(key="client_form"):
    name = st.text_input("Client Name")
    email = st.text_input("Email Address")
    sessions_booked = st.number_input("Number of Sessions Booked", min_value=0, value=12)
    submit_button = st.form_submit_button("Add Client")

    if submit_button:
        if name and email:  # Make sure both name and email are provided
            if name not in st.session_state.clients:
                st.session_state.clients[name] = {
                    "email": email,
                    "sessions_completed": 0,
                    "sessions_remaining": sessions_booked,
                    "total_sessions": sessions_booked,
                    "booked_sessions": [],
                }
                save_clients_to_csv(st.session_state.clients)
                st.success(f"Client {name} added successfully!")
            else:
                st.warning(f"Client {name} already exists!")
        else:
            st.warning("Please provide both name and email")

# Session Tracking Section
st.header("Track Sessions")

if st.session_state.clients:
    for client, data in st.session_state.clients.items():
        st.write(f"Client: {client}")
        st.write(f"Email: {data['email']}")
        st.write(f"Sessions Completed: {data['sessions_completed']}")
        st.write(f"Sessions Remaining: {data['sessions_remaining']}")

        # Display booked sessions
        booked_sessions = data.get("booked_sessions", [])
        st.write("Upcoming Booked Sessions:")
        if booked_sessions:
            booked_sessions.sort()
            for session in booked_sessions:
                try:
                    session_date = datetime.strptime(session, '%Y-%m-%d').strftime('%B %d, %Y')
                    st.write(f"- {session_date}")
                except ValueError:
                    st.write(f"- {session}")
        else:
            st.write("No upcoming sessions. Start booking now!")
        st.write("---")
else:
    st.info("No clients available. Please add new clients.")

# Session Booking Section
st.header("Session Booking")

if st.session_state.clients:
    selected_client = st.selectbox("Select Client for Booking", st.session_state.clients.keys())
    booking_date = st.date_input("Select a Date for Booking")

    if st.button("Book Session"):
        if selected_client:
            date_str = booking_date.strftime('%Y-%m-%d')
            if date_str not in st.session_state.clients[selected_client]["booked_sessions"]:
                st.session_state.clients[selected_client]["booked_sessions"].append(date_str)
                save_clients_to_csv(st.session_state.clients)
                st.success(f"Session booked for {selected_client} on {booking_date.strftime('%B %d, %Y')}")
            else:
                st.warning(f"{selected_client} already has a session booked on {booking_date.strftime('%B %d, %Y')}.")
else:
    st.info("No clients available. Please add clients first.")

# Update Sessions for a Specific Client
st.header("Update Client Sessions")

if st.session_state.clients:
    update_client = st.selectbox(
        "Select Client to Update",
        st.session_state.clients.keys(),
        key="update_client"
    )

    if update_client:
        client_data = st.session_state.clients[update_client]
        st.write(f"Client: {update_client}")
        st.write(f"Sessions Completed: {client_data['sessions_completed']}")
        st.write(f"Sessions Remaining: {client_data['sessions_remaining']}")

        # Display upcoming sessions
        booked_sessions = client_data.get("booked_sessions", [])
        st.write("Upcoming Booked Sessions:")
        if booked_sessions:
            booked_sessions.sort()
            for session in booked_sessions:
                try:
                    session_date = datetime.strptime(session, '%Y-%m-%d').strftime('%B %d, %Y')
                    st.write(f"- {session_date}")
                except ValueError:
                    st.write(f"- {session}")
        else:
            st.write("No upcoming sessions. Start booking now!")

        if st.button("Mark Session as Completed"):
            if client_data['sessions_remaining'] > 0:
                if booked_sessions:
                    completed_date = booked_sessions.pop(0)
                    client_data["sessions_completed"] += 1
                    client_data["sessions_remaining"] -= 1
                    save_clients_to_csv(st.session_state.clients)
                    st.success(f"Session marked as completed!")
                else:
                    st.info("No booked sessions to mark as completed.")
            else:
                st.warning(f"{update_client} has no remaining sessions.")

# Payment Reminder Section
st.header("Payment Reminders")

if st.session_state.clients:
    for client, data in st.session_state.clients.items():
        if data["sessions_remaining"] == 0:
            st.warning(f"Payment Reminder: {client} has completed all sessions. Please request payment.")
else:
    st.info("No clients to check for payment reminders.")
```