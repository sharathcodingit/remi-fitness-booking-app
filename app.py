import streamlit as st
import pandas as pd
from datetime import datetime
import os
from git import Repo
import traceback

# Constants
FILE_NAME = "clients.csv"
REPO_PATH = "/mount/src/remi-fitness-booking-app"
FULL_PATH = os.path.join(REPO_PATH, FILE_NAME)

# Debug information
print(f"Starting app with:")
print(f"Repo path: {REPO_PATH}")
print(f"CSV path: {FULL_PATH}")
print(f"File exists: {os.path.exists(FULL_PATH)}")

def sync_with_github():
    """Function to sync changes with GitHub"""
    try:
        # Use the mounted directory path
        repo_path = "/mount/src/remi-fitness-booking-app"
        repo = Repo(repo_path)
        
        print(f"Starting sync from {repo_path}")
        
        # Add specific file instead of all changes
        print("Adding clients.csv to git")
        repo.git.add('clients.csv')
        
        try:
            # Check if there are changes to commit
            if repo.is_dirty(path='clients.csv'):
                print("Changes detected, committing")
                repo.index.commit("Updated client data")
                
                print("Pulling latest changes")
                repo.git.pull('origin', 'main', rebase=False)
                
                print("Pushing changes")
                origin = repo.remote('origin')
                origin.push()
                
                print("Sync completed successfully")
                return True
            else:
                print("No changes to sync in clients.csv")
                return True
        except Exception as git_error:
            print(f"Git operation error: {str(git_error)}")
            return False
            
    except Exception as e:
        print(f"Sync error: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error trace: {traceback.format_exc()}")
        return False

def load_clients_from_csv(file_name=FILE_NAME):
    """Function to load client data from CSV"""
    try:
        if os.path.exists(file_name):
            print(f"Loading clients from {file_name}")
            df = pd.read_csv(file_name)
            if 'client_name' in df.columns:
                df.set_index('client_name', inplace=True)
            
            # Convert 'booked_sessions' from string to list
            df["booked_sessions"] = df["booked_sessions"].apply(
                lambda x: eval(x) if pd.notna(x) and x != '[]' else []
            )
            data = df.to_dict(orient="index")
            print(f"Loaded clients: {list(data.keys())}")
            return data
        else:
            print(f"No existing {file_name} found. A new one will be created.")
            return {}
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        print(traceback.format_exc())
        return {}

def save_clients_to_csv(clients, file_name=FILE_NAME):
    """Function to save client data to CSV and sync with GitHub"""
    try:
        print(f"Starting save operation for {len(clients)} clients")
        
        # Create a copy of the clients dictionary
        clients_copy = {
            client: {**data, 'booked_sessions': str(data['booked_sessions'])}
            for client, data in clients.items()
        }
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(clients_copy, orient="index")
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'client_name'}, inplace=True)
        
        # Get full path for saving
        full_path = os.path.join("/mount/src/remi-fitness-booking-app", file_name)
        print(f"Saving to: {full_path}")
        
        # Save CSV
        df.to_csv(full_path, index=False)
        
        # Verify save
        if os.path.exists(full_path):
            print(f"Successfully saved {len(clients)} clients")
            
            # Attempt sync
            if sync_with_github():
                st.success("✅ Changes saved and synced with GitHub!")
                return True
            else:
                st.warning("💾 Changes saved locally but GitHub sync failed.")
                st.info("Click 'Manual Sync' below to retry syncing.")
                return False
        else:
            st.error("❌ Failed to save changes!")
            return False
            
    except Exception as e:
        print(f"Save error: {str(e)}")
        print(f"Error trace: {traceback.format_exc()}")
        st.error(f"Error saving data: {str(e)}")
        return False

# Initialize clients in session state
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_from_csv()
    print("Initialized clients:", list(st.session_state.clients.keys()))

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
                try:
                    # Add new client
                    st.session_state.clients[name] = {
                        "email": email,
                        "sessions_completed": 0,
                        "sessions_remaining": sessions_booked,
                        "total_sessions": sessions_booked,
                        "booked_sessions": [],
                    }
                    
                    # Debug print
                    print(f"Adding new client: {name}")
                    print("Current clients:", st.session_state.clients)
                    
                    # Save and sync
                    save_clients_to_csv(st.session_state.clients)
                    st.success(f"Client {name} added successfully!")
                    
                    # Verify save
                    if os.path.exists(FILE_NAME):
                        df = pd.read_csv(FILE_NAME)
                        st.write("Current clients in CSV:", df['client_name'].tolist())
                    else:
                        st.error("CSV file not found after save!")
                        
                except Exception as e:
                    st.error(f"Error adding client: {str(e)}")
                    print(f"Error details: {str(e)}")
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

        # Display booked sessions with updated message
        booked_sessions = data.get("booked_sessions", [])
        st.write("Upcoming Booked Sessions:")
        if booked_sessions:
            # Sort sessions by date
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

        # Display upcoming sessions with proper date formatting
        booked_sessions = client_data.get("booked_sessions", [])
        st.write("Upcoming Booked Sessions:")
        if booked_sessions:
            # Sort sessions by date
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
                    # Remove the earliest booked session
                    completed_date = booked_sessions.pop(0)
                    try:
                        display_date = datetime.strptime(completed_date, '%Y-%m-%d').strftime('%B %d, %Y')
                    except ValueError:
                        display_date = completed_date
                    
                    # Update session counts
                    client_data["sessions_completed"] += 1
                    client_data["sessions_remaining"] -= 1
                    
                    # Save and sync updates
                    save_clients_to_csv(st.session_state.clients)
                    st.success(f"Session on {display_date} marked as completed!")
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

# Manual Sync Button
st.header("Manual Sync")
if st.button("Sync with GitHub"):
    if sync_with_github():
        st.success("Successfully synced with GitHub!")
    else:
        st.error("Failed to sync with GitHub. Check the logs for details.")
