import streamlit as st
import pandas as pd

# CSV file name
FILE_NAME = "clients.csv"

# Function to load client data from a CSV file
def load_clients_from_csv(file_name=FILE_NAME):
    try:
        df = pd.read_csv(file_name, index_col=0)
        # Convert 'booked_sessions' from string to list
        df["booked_sessions"] = df["booked_sessions"].apply(
            lambda x: eval(x) if pd.notna(x) else []
        )
        return df.to_dict(orient="index")  # Convert DataFrame to dictionary
    except FileNotFoundError:
        return {}

# Function to save client data to a CSV file
def save_clients_to_csv(clients, file_name=FILE_NAME):
    # Convert 'booked_sessions' to a string for saving
    for client in clients.values():
        client["booked_sessions"] = str(client["booked_sessions"])
    df = pd.DataFrame.from_dict(clients, orient="index")
    df.to_csv(file_name)

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
            "booked_sessions": [],  # New field for session booking
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

        # Check if booked_sessions is empty
        booked_sessions = data.get("booked_sessions", [])
        if booked_sessions:
            st.write("Booked Sessions:")
            for session in booked_sessions:
                st.write(f"- {session}")
        else:
            st.write("No sessions booked.")
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
            if booking_date not in st.session_state.clients[selected_client]["booked_sessions"]:
                st.session_state.clients[selected_client]["booked_sessions"].append(str(booking_date))
                save_clients_to_csv(st.session_state.clients)
                st.success(f"Session booked for {selected_client} on {booking_date}")
            else:
                st.warning(f"{selected_client} already has a session booked on {booking_date}.")
else:
    st.info("No clients available. Please add clients first.")

# Update Sessions for a Specific Client
st.header("Update Client Sessions")

if st.session_state.clients:
    selected_client = st.selectbox("Select Client to Update", st.session_state.clients.keys())

    if selected_client:
        st.write(f"Client: {selected_client}")
        st.write(f"Sessions Completed: {st.session_state.clients[selected_client]['sessions_completed']}")
        st.write(f"Sessions Remaining: {st.session_state.clients[selected_client]['sessions_remaining']}")
        upcoming_sessions = st.session_state.clients[selected_client]["booked_sessions"]

        if not upcoming_sessions:
            st.write("Upcoming Booked Sessions: No upcoming sessions. Start booking now!")
        else:
            st.write(f"Upcoming Booked Sessions: {upcoming_sessions}")

        if st.button("Mark Session as Completed"):
            if st.session_state.clients[selected_client]['sessions_remaining'] > 0:
                if st.session_state.clients[selected_client]["booked_sessions"]:
                    # Ensure "booked_sessions" is a list, not a string
                    if isinstance(st.session_state.clients[selected_client]["booked_sessions"], str):
                        # Convert it to a list (assuming it was stored as a comma-separated string)
                        st.session_state.clients[selected_client]["booked_sessions"] = st.session_state.clients[selected_client]["booked_sessions"].split(",")

                    # Safely pop the first session
                    if st.session_state.clients[selected_client]["booked_sessions"]:
                        completed_date = st.session_state.clients[selected_client]["booked_sessions"].pop(0)
                        st.success(f"Session on {completed_date} marked as completed!")

                        # **Update counters only here**
                        st.session_state.clients[selected_client]["sessions_completed"] += 1
                        st.session_state.clients[selected_client]["sessions_remaining"] -= 1

                        # Save updates
                        save_clients_to_csv(st.session_state.clients)

                    else:
                        st.info("No booked sessions to mark as completed.")
                else:
                    st.warning(f"{selected_client} has no remaining sessions.")
            else:
                st.info("No clients available to update.")

# Payment Reminder Section
st.header("Payment Reminders")

if st.session_state.clients:
    for client, data in st.session_state.clients.items():
        if data["sessions_remaining"] == 0:
            st.warning(f"Payment Reminder: {client} has completed all sessions. Please request payment.")
else:
    st.info("No clients to check for payment reminders.")
