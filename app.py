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
if 'is_trainer' not in st.session_state:
    st.session_state.is_trainer = False

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

def save_clients_to_csv(clients, file_name=FILE_NAME):
    """Function to save client data to CSV"""
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
        
        df.to_csv(file_name, index=False)
        st.success("Changes saved successfully!")
        sync_with_github()
        
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

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

def display_calendar_view():
    """Display the calendar view for the trainer"""
    st.header("Session Calendar")
    
    # Calendar navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Previous Week"):
            st.session_state.selected_date -= timedelta(days=7)
    with col2:
        st.write(f"Week of {st.session_state.selected_date.strftime('%B %d, %Y')}")
    with col3:
        if st.button("Next Week →"):
            st.session_state.selected_date += timedelta(days=7)
    
    # Get the start of the week
    start_of_week = st.session_state.selected_date - timedelta(days=st.session_state.selected_date.weekday())
    
    # Create weekly calendar
    week_days = []
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        week_days.append(current_date)
    
    # Display calendar grid
    cols = st.columns(7)
    for i, day in enumerate(week_days):
        with cols[i]:
            st.write(f"**{day.strftime('%a %b %d')}**")
            
            # Display booked sessions for this day
            for client_name, client_data in st.session_state.clients.items():
                for session in client_data['booked_sessions']:
                    session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                    if session_datetime.date() == day.date():
                        st.info(f"{session_datetime.strftime('%I:%M %p')}\n{client_name}")

def display_client_management():
    """Display the client management interface"""
    st.header("Client Management")
    
    # Add new client form
    with st.form("add_client_form"):
        st.subheader("Add New Client")
        new_client_name = st.text_input("Client Name")
        new_client_email = st.text_input("Email")
        new_client_sessions = st.number_input("Number of Sessions", min_value=1, value=12)
        
        if st.form_submit_button("Add Client"):
            if new_client_name and new_client_email:
                if new_client_name not in st.session_state.clients:
                    st.session_state.clients[new_client_name] = {
                        'email': new_client_email,
                        'sessions_completed': 0,
                        'sessions_remaining': new_client_sessions,
                        'total_sessions': new_client_sessions,
                        'booked_sessions': []
                    }
                    save_clients_to_csv(st.session_state.clients)
                    st.success(f"Client {new_client_name} added successfully!")
                else:
                    st.error(f"Client {new_client_name} already exists!")
            else:
                st.error("Please provide both name and email")

    # Manage existing clients
    st.subheader("Manage Existing Clients")
    for client_name, data in st.session_state.clients.items():
        with st.expander(f"{client_name} - {data['sessions_remaining']} sessions remaining"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"Email: {data['email']}")
                st.write(f"Sessions Completed: {data['sessions_completed']}")
                st.write(f"Total Sessions: {data['total_sessions']}")
                
                if st.button(f"Mark Session Complete for {client_name}", key=f"complete_{client_name}"):
                    if data['sessions_remaining'] > 0:
                        data['sessions_completed'] += 1
                        data['sessions_remaining'] -= 1
                        save_clients_to_csv(st.session_state.clients)
                        st.success("Session marked as completed!")
                    else:
                        st.error("No remaining sessions!")
            
            with col2:
                st.write("Upcoming Sessions:")
                upcoming = []
                for session in data['booked_sessions']:
                    session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                    if session_datetime > datetime.now():
                        upcoming.append(session_datetime)
                
                if upcoming:
                    for session in sorted(upcoming):
                        st.write(f"- {session.strftime('%B %d, %Y at %I:%M %p')}")
                else:
                    st.write("No upcoming sessions")

def display_reports():
    """Display the reports interface"""
    st.header("Reports")
    
    # Summary statistics
    st.subheader("Summary Statistics")
    total_clients = len(st.session_state.clients)
    total_sessions = sum(client['sessions_completed'] for client in st.session_state.clients.values())
    active_clients = sum(1 for client in st.session_state.clients.values() if client['sessions_remaining'] > 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clients", total_clients)
    with col2:
        st.metric("Active Clients", active_clients)
    with col3:
        st.metric("Total Sessions Completed", total_sessions)
    
    # Sessions by client chart
    st.subheader("Sessions by Client")
    sessions_data = {
        client_name: {
            'completed': data['sessions_completed'],
            'remaining': data['sessions_remaining']
        }
        for client_name, data in st.session_state.clients.items()
    }
    
    # Convert to DataFrame for display
    df = pd.DataFrame([
        {
            'Client': name,
            'Completed Sessions': data['completed'],
            'Remaining Sessions': data['remaining']
        }
        for name, data in sessions_data.items()
    ])
    
    st.write(df)
    
    # Export options
    st.subheader("Export Data")
    if st.button("Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "fitness_trainer_report.csv",
            "text/csv",
            key='download-csv'
        )

def display_client_booking():
    """Display the client booking interface"""
    st.title("Book Your Session")
    
    # Check if we have any clients
    if not st.session_state.clients:
        st.warning("No clients registered yet. Please contact your trainer.")
        return
    
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
    if st.session_state.authenticated_client and st.session_state.authenticated_client in st.session_state.clients:
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
                        try:
                            booked_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                            if abs((slot_datetime - booked_datetime).total_seconds()) < 3600:
                                slot_is_available = False
                                break
                        except ValueError:
                            continue
                
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
                try:
                    session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                    if session_datetime > datetime.now():
                        upcoming_sessions.append(session_datetime)
                except ValueError:
                    continue
            
            if upcoming_sessions:
                for session in sorted(upcoming_sessions):
                    st.write(f"📅 {session.strftime('%B %d, %Y at %I:%M %p')}")
            else:
                st.write("No upcoming sessions")
                
        else:
            st.warning("You have no remaining sessions. Please contact your trainer to purchase more sessions.")
        
        # Logout button
        if st.button("Logout"):
            st.session_state.authenticated_client = None
            st.experimental_rerun()
    else:
        # If somehow the authentication state is invalid, reset it
        st.session_state.authenticated_client = None
        st.experimental_rerun()

def main():
    st.set_page_config(page_title="Fitness Training App", page_icon="💪")
    
    # Load client data
    if not st.session_state.clients:
        st.session_state.clients = load_clients_from_csv()
    
    # Navigation
    st.sidebar.title("Navigation")
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