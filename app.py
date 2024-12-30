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
        if 'SECRET_TOKEN' in st.secrets:
            token = st.secrets['SECRET_TOKEN']
            repo = Repo(REPO_PATH)
            
            try:
                remote_url = f'https://{token}@github.com/sharathcodingit/remi-fitness-booking-app.git'
                repo.git.remote('set-url', 'origin', remote_url)
                repo.git.add('--force', FILE_NAME)
                
                if repo.is_dirty(untracked_files=True):
                    repo.index.commit(commit_message)
                    repo.git.pull('--rebase', 'origin', 'main')
                    repo.git.push('--force-with-lease', 'origin', 'main')
                    print("GitHub sync completed successfully")
                    return True
                else:
                    print("No changes to commit")
                    return True
                    
            except Exception as e:
                print(f"Git operation error: {str(e)}")
                repo.git.reset('--hard')
                return False
                
        else:
            print("SECRET_TOKEN not found in Streamlit secrets")
            return False
            
    except Exception as e:
        print(f"GitHub sync error: {str(e)}")
        print(traceback.format_exc())
        return False

def load_clients_from_csv(file_name=FILE_NAME):
    """Function to load client data from CSV with robust error handling"""
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype=str)
            clients_dict = {}
            
            required_columns = ['client_name', 'email', 'sessions_completed', 
                              'sessions_remaining', 'total_sessions', 'booked_sessions']
            
            if not all(col in df.columns for col in required_columns):
                print(f"Missing required columns. Found columns: {df.columns.tolist()}")
                return {}
            
            for _, row in df.iterrows():
                try:
                    client_name = row['client_name'].strip()
                    if not client_name:
                        continue
                        
                    sessions_completed = int(float(row['sessions_completed'])) if pd.notna(row['sessions_completed']) else 0
                    sessions_remaining = int(float(row['sessions_remaining'])) if pd.notna(row['sessions_remaining']) else 0
                    total_sessions = int(float(row['total_sessions'])) if pd.notna(row['total_sessions']) else 0
                    
                    try:
                        booked_sessions = eval(row['booked_sessions']) if pd.notna(row['booked_sessions']) and row['booked_sessions'].strip() not in ('[]', '') else []
                        if not isinstance(booked_sessions, list):
                            booked_sessions = []
                    except:
                        booked_sessions = []
                    
                    clients_dict[client_name] = {
                        'email': row['email'].strip() if pd.notna(row['email']) else '',
                        'sessions_completed': sessions_completed,
                        'sessions_remaining': sessions_remaining,
                        'total_sessions': total_sessions,
                        'booked_sessions': booked_sessions
                    }
                except Exception as row_error:
                    print(f"Error processing row: {row}\nError: {str(row_error)}")
                    continue
                    
            return clients_dict
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        if 'df' in locals():
            print(f"DataFrame head:\n{df.head()}")
            print(f"DataFrame columns: {df.columns.tolist()}")
    return {}

def save_clients_to_csv(clients, file_name=FILE_NAME):
    """Function to save client data to CSV and sync with GitHub"""
    try:
        clients_copy = {}
        for name, data in clients.items():
            clients_copy[name] = data.copy()
            clients_copy[name]['booked_sessions'] = str(data['booked_sessions'])
        
        df = pd.DataFrame.from_dict(clients_copy, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'client_name'}, inplace=True)
        
        columns = ['client_name', 'email', 'sessions_completed', 'sessions_remaining', 
                  'total_sessions', 'booked_sessions']
        df = df[columns]
        
        temp_file = file_name + '.tmp'
        df.to_csv(temp_file, index=False)
        os.replace(temp_file, file_name)
        
        sync_success = sync_with_github()
        
        if not sync_success:
            print("First sync attempt failed, retrying...")
            sync_success = sync_with_github()
        
        if sync_success:
            st.success("Changes saved and synced successfully!")
        else:
            st.warning("Changes saved locally but GitHub sync failed. Please commit manually.")
            
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        print(f"Error details: {str(e)}")
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass

# Initialize clients in session state
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_from_csv()

# App title
st.title("Fitness Trainer App")
st.write("Welcome! Use this app to manage client sessions, bookings, and payments.")

# Client Onboarding Section
st.header("Add a New Client")

with st.form(key="client_form"):
    name = st.text_input("Client Name")
    email = st.text_input("Email Address")
    sessions_booked = st.number_input("Number of Sessions Booked", min_value=0, value=12)
    submit_button = st.form_submit_button("Add Client")

    if submit_button:
        if name and email:
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

# Session Booking Section
st.header("Session Booking")

if st.session_state.clients:
    sorted_client_names = sorted(st.session_state.clients.keys())
    selected_client = st.selectbox("Select Client for Booking", sorted_client_names)
    booking_date = st.date_input("Select a Date for Booking")
    booking_time = st.time_input("Select Time for Booking")

    if st.button("Book Session"):
        if selected_client:
            current_date = datetime.now().date()
            if booking_date < current_date:
                st.error("Cannot book sessions for past dates.")
            else:
                datetime_str = f"{booking_date.strftime('%Y-%m-%d')} {booking_time.strftime('%H:%M')}"
                if datetime_str not in st.session_state.clients[selected_client]["booked_sessions"]:
                    st.session_state.clients[selected_client]["booked_sessions"].append(datetime_str)
                    save_clients_to_csv(st.session_state.clients)
                    st.success(f"Session booked for {selected_client} on {booking_date.strftime('%B %d, %Y')} at {booking_time.strftime('%I:%M %p')}")
                else:
                    st.warning(f"{selected_client} already has a session booked on {booking_date.strftime('%B %d, %Y')} at {booking_time.strftime('%I:%M %p')}.")
else:
    st.info("No clients available. Please add clients first.")

# Update Sessions for a Specific Client
st.header("Update Client Sessions")

if st.session_state.clients:
    sorted_client_names = sorted(st.session_state.clients.keys())
    update_client = st.selectbox(
        "Select Client to Update",
        sorted_client_names,
        key="update_client"
    )

    if update_client:
        client_data = st.session_state.clients[update_client]
        st.write(f"Client: {update_client}")
        st.write(f"Sessions Completed: {client_data['sessions_completed']}")
        st.write(f"Sessions Remaining: {client_data['sessions_remaining']}")

        booked_sessions = client_data.get("booked_sessions", [])
        st.write("Upcoming Booked Sessions:")
        if booked_sessions:
            booked_sessions.sort()
            for session in booked_sessions:
                try:
                    # Try to parse the datetime string
                    session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                    st.write(f"- {session_datetime.strftime('%B %d, %Y at %I:%M %p')}")
                except ValueError:
                    # If parsing fails, display the original string
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
    has_reminders = False
    for client, data in sorted(st.session_state.clients.items()):
        if data["sessions_remaining"] == 0:
            has_reminders = True
            st.warning(f"Payment Reminder: {client} has completed all sessions. Please request payment.")
    
    if not has_reminders:
        st.success("No payment reminders needed at this time.")
else:
    st.info("No clients to check for payment reminders.")