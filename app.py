import streamlit as st
import pandas as pd
from datetime import datetime
import os

# CSV file name
FILE_NAME = "clients.csv"

# Function to load client data from a CSV file
def load_clients_from_csv(file_name=FILE_NAME):
    try:
        df = pd.read_csv(file_name, index_col=0)
        # Convert 'booked_sessions' from string to list
        df["booked_sessions"] = df["booked_sessions"].apply(
            lambda x: eval(x) if pd.notna(x) and x != '[]' else []
        )
        return df.to_dict(orient="index")
    except FileNotFoundError:
        st.info(f"No existing {file_name} found. A new one will be created.")
        return {}
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return {}

# Function to save client data to a CSV file
def save_clients_to_csv(clients, file_name=FILE_NAME):
    try:
        # Create a copy of the clients dictionary
        clients_copy = {
            client: {**data, 'booked_sessions': str(data['booked_sessions'])}
            for client, data in clients.items()
        }
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(clients_copy, orient="index")
        
        # Save CSV with index
        df.to_csv(file_name)
        print(f"Saved {len(clients)} clients to {file_name}")  # Debug print
    except Exception as e:
        st.error(f"Error saving to CSV: {str(e)}")
        print(f"Error saving CSV: {str(e)}")  # Debug print

# In the client onboarding section, modify the submit button handler:
if submit_button:
    if name and email:  # Make sure both name and email are provided
        if name not in st.session_state.clients:
            # Add new client
            st.session_state.clients[name] = {
                "email": email,
                "sessions_completed": 0,
                "sessions_remaining": sessions_booked,
                "total_sessions": sessions_booked,
                "booked_sessions": [],
            }
            
            # Save immediately after adding
            try:
                save_clients_to_csv(st.session_state.clients)
                st.success(f"Client {name} added successfully!")
                
                # Debug information
                st.write("Current clients:", list(st.session_state.clients.keys()))
            except Exception as e:
                st.error(f"Failed to save client data: {str(e)}")
        else:
            st.warning(f"Client {name} already exists!")
    else:
        st.warning("Please provide both name and email")

# Initialize clients in session state
if "clients" not in st.session_state:
    st.session_state.clients = load_clients_from_csv()

# App title
st.title("Fitness Trainer App")

# Introduction
st.write("Welcome! Use this app to manage client sessions, bookings, and payments.")

# Client Onboarding Section
st.header("Add a New Client")

with st.form("client_form"):
    name = st.text_input("Client Name")
    email = st.text_input("Email Address")
    sessions_booked = st.number_input("Number of Sessions Booked", min_value=0, value=12)
    submit_button = st.form_submit_button("Add Client")

if submit_button:
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
                # Format the date for display
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
                    
                    # Save updates
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