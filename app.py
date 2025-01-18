import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from git import Repo
import traceback
import calendar

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
        
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

def display_calendar_view():
    """Display the calendar view for booking sessions"""
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
    st.write("---")
    cols = st.columns(7)
    for i, day in enumerate(week_days):
        with cols[i]:
            st.write(day.strftime("%a\n%b %d"))
            
            # Display time slots for each day
            for hour in range(9, 18):  # 9 AM to 5 PM
                time_slot = f"{hour:02d}:00"
                is_slot_booked = False
                booked_client = None
                
                # Check if slot is booked
                for client, data in st.session_state.clients.items():
                    for session in data['booked_sessions']:
                        session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                        if (session_datetime.date() == day.date() and 
                            session_datetime.strftime('%H:%M') == time_slot):
                            is_slot_booked = True
                            booked_client = client
                            break
                
                if is_slot_booked:
                    st.write(f"🔴 {time_slot}\n{booked_client}")
                else:
                    if st.button(f"📅 {time_slot}", key=f"{day.date()}_{time_slot}"):
                        book_session(day, time_slot)

def book_session(date, time_slot):
    """Book a session for a client"""
    # Client selection
    client_names = list(st.session_state.clients.keys())
    if not client_names:
        st.error("No clients available. Please add clients first.")
        return
    
    selected_client = st.selectbox("Select Client", client_names)
    
    if selected_client:
        client_data = st.session_state.clients[selected_client]
        if client_data['sessions_remaining'] <= 0:
            st.error(f"{selected_client} has no remaining sessions.")
            return
        
        # Create datetime for the booking
        booking_datetime = datetime.combine(date, datetime.strptime(time_slot, '%H:%M').time())
        datetime_str = booking_datetime.strftime('%Y-%m-%d %H:%M')
        
        # Check for conflicts
        for client, data in st.session_state.clients.items():
            for session in data['booked_sessions']:
                existing_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                if abs((booking_datetime - existing_datetime).total_seconds()) < 3600:
                    st.error("This time slot is already booked.")
                    return
        
        # Book the session
        client_data['booked_sessions'].append(datetime_str)
        save_clients_to_csv(st.session_state.clients)
        st.success(f"Session booked for {selected_client} on {date.strftime('%B %d, %Y')} at {time_slot}")

def display_client_management():
    """Display the client management section"""
    st.header("Client Management")
    
    # Add new client
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

    # Display existing clients
    st.subheader("Existing Clients")
    for client_name, data in st.session_state.clients.items():
        with st.expander(f"{client_name} - {data['sessions_remaining']} sessions remaining"):
            st.write(f"Email: {data['email']}")
            st.write(f"Sessions Completed: {data['sessions_completed']}")
            st.write(f"Total Sessions: {data['total_sessions']}")
            
            # Display upcoming sessions
            if data['booked_sessions']:
                st.write("Upcoming Sessions:")
                for session in sorted(data['booked_sessions']):
                    session_datetime = datetime.strptime(session, '%Y-%m-%d %H:%M')
                    if session_datetime > datetime.now():
                        st.write(f"- {session_datetime.strftime('%B %d, %Y at %I:%M %p')}")

def main():
    st.title("Fitness Trainer App")
    
    # Navigation
    st.sidebar.title("Navigation")
    view = st.sidebar.radio("Go to", ['Calendar', 'Clients', 'Reports'])
    
    # Load client data
    if not st.session_state.clients:
        st.session_state.clients = load_clients_from_csv()
    
    # Display selected view
    if view == 'Calendar':
        display_calendar_view()
    elif view == 'Clients':
        display_client_management()
    else:  # Reports
        st.header("Reports")
        # Add reporting functionality here
        
if __name__ == "__main__":
    main()