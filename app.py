import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from git import Repo
import traceback

# Constants
FILE_NAME = "clients.csv"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

# Initialize session state variables
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'calendar'
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now()
if 'clients' not in st.session_state:
    st.session_state.clients = {}
if 'authenticated_client' not in st.session_state:
    st.session_state.authenticated_client = None

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
                    return True
                else:
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
    """Function to load client data from CSV"""
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, dtype=str)
            clients_dict = {}
            
            required_columns = ['client_name', 'email', 'sessions_completed', 
                              'sessions_remaining', 'total_sessions', 'booked_sessions']
            
            if not all(col in df.columns for col in required_columns):
                st.error(f"Missing required columns. Found columns: {df.columns.tolist()}")
                return {}
            
            for _, row in df.iterrows():
                client_name = row['client_name'].strip()
                if not client_name:
                    continue
                    
                sessions_completed = int(float(row['sessions_completed'])) if pd.notna(row['sessions_completed']) else 0
                sessions_remaining = int(float(row['sessions_remaining'])) if pd.notna(row['sessions_remaining']) else 0
                total_sessions = int(float(row['total_sessions'])) if pd.notna(row['total_sessions']) else 0
                
                try:
                    booked_sessions = eval(row['booked_sessions']) if pd.notna(row['booked_sessions']) and row['booked_sessions'].strip() not in ('[]', '') else []
                except:
                    booked_sessions = []
                
                clients_dict[client_name] = {
                    'email': row['email'].strip() if pd.notna(row['email']) else '',
                    'sessions_completed': sessions_completed,
                    'sessions_remaining': sessions_remaining,
                    'total_sessions': total_sessions,
                    'booked_sessions': booked_sessions
                }
            return clients_dict
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
    return {}

def display_client_booking():
    """Display the client booking interface"""
    st.title("Book Your Session")
    
    # Client Login
    if not st.session_state.authenticated_client:
        st.header("Client Login")
        email = st.text_input("Enter your email")
        
        if email:
            # Find client by email
            client_found = False
            for client_name, data in st.session_state.clients.items():
                if data['email'].lower() == email.lower():
                    st.session_state.authenticated_client = client_name
                    client_found = True
                    break
            
            if not client_found:
                st.error("Email not found. Please check your email or contact your trainer.")
                return
    
    # Show booking interface for authenticated client
    if st.session_state.authenticated_client:
        client_data = st.session_state.clients[st.session_state.authenticated_client]
        st.success(f"Welcome, {st.session_state.authenticated_client}!")
        
        # Show remaining sessions
        sessions_remaining = client_data['sessions_remaining']
        st.info(f"You have {sessions_remaining} sessions remaining")
        
        if sessions_remaining > 0:
            st.header("Book a Session")
            
            # Date selection
            min_date = datetime.now().date()
            max_date = min_date + timedelta(days=30)
            selected_date = st.date_input(
                "Select Date",
                min_value=min_date,
                max_value=max_date,
                value=min_date
            )
            
            # Time selection
            available_times = []
            for hour in range(9, 18):  # 9 AM to 5 PM
                time_slot = f"{hour:02d}:00"
                
                # Check if slot is available
                slot_datetime = datetime.combine(selected_date, datetime.strptime(time_slot, '%H:%M').time())
                slot_is_available = True
                
                for _, data in st.session_state.clients.items():
                    for session in data['booked_sessions']:
                        booked_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                        if abs((slot_datetime - booked_datetime).total_seconds()) < 3600:
                            slot_is_available = False
                            break
                
                if slot_is_available:
                    available_times.append(time_slot)
            
            if available_times:
                selected_time = st.selectbox(
                    "Select Time",
                    available_times,
                    format_func=lambda x: f"{x} - {(datetime.strptime(x, '%H:%M') + timedelta(hours=1)).strftime('%H:%M')}"
                )
                
                if st.button("Book Session"):
                    booking_datetime = datetime.combine(selected_date, datetime.strptime(selected_time, '%H:%M').time())
                    
                    if booking_datetime < datetime.now():
                        st.error("Cannot book sessions in the past!")
                    else:
                        client_data['booked_sessions'].append(booking_datetime.strftime('%Y-%m-%d %H:%M'))
                        save_clients_to_csv(st.session_state.clients)
                        st.success(f"Session booked for {selected_date.strftime('%B %d, %Y')} at {selected_time}")
                        st.balloons()
            else:
                st.warning("No available time slots for the selected date. Please try another date.")
            
            # Show upcoming bookings
            st.header("Your Upcoming Sessions")
            upcoming_sessions = []
            for session in client_data['booked_sessions']:
                session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                if session_datetime > datetime.now():
                    upcoming_sessions.append(session_datetime)
            
            if upcoming_sessions:
                for session in sorted(upcoming_sessions):
                    st.write(f"📅 {session.strftime('%B %d, %Y at %I:%M %p')}")
            else:
                st.info("No upcoming sessions")
        else:
            st.warning("You have no remaining sessions. Please contact your trainer to purchase more sessions.")
        
        # Logout button
        if st.button("Logout"):
            st.session_state.authenticated_client = None
            st.experimental_rerun()

def main():
    st.set_page_config(page_title="Fitness Training App", page_icon="💪")
    
    # Load client data
    if not st.session_state.clients:
        st.session_state.clients = load_clients_from_csv()
    
    # Navigation
    st.sidebar.title("Navigation")
    if 'is_trainer' not in st.session_state:
        st.session_state.is_trainer = st.sidebar.checkbox("I am the trainer")
    
    if st.session_state.is_trainer:
        view = st.sidebar.radio("Go to", ['Calendar', 'Clients', 'Reports'])
        
        if view == 'Calendar':
            display_calendar_view()
        elif view == 'Clients':
            display_client_management()
        else:  # Reports
            display_reports()
    else:
        display_client_booking()

if __name__ == "__main__":
    main()