import streamlit as st
import json
import time
from streamlit_extras.switch_page_button import switch_page
from hashlib import sha256


def conditionally_hide_sidebar():
    if "username" in st.session_state and st.session_state["username"]:
        # User is logged in: Show full sidebar
        return False
    else:
        # User is not logged in: Keep sidebar visible but hide additional content
        hide_sidebar_style = """
            <style>
            [data-testid="stSidebarNav"] {display: none;} /* Hides sidebar nav elements */
            </style>
        """
        st.markdown(hide_sidebar_style, unsafe_allow_html=True)
        return True

# Call the function in your app
conditionally_hide_sidebar()


# Load or initialize user data
def load_user_data():
    try:
        with open("database.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open("database.json", "w") as f:
        json.dump(data, f)

# Hash password
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Registration
def register():
    st.title("Register")
    username = st.text_input("Username", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")
    user_data = load_user_data()

    if st.button("Register"):
        if username in user_data:
            st.error("Username already exists.")
        elif any(user['email'] == email for user in user_data.values()):
            st.error("Email already exists.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters long.")
        else:
            user_data[username] = {
                "email": email,
                "password": hash_password(password),
                "chatbots": []
            }
            save_user_data(user_data)
            st.success("Registration successful! Please log in.")
            switch_page("login")

# Login
def login():
    st.title("Login")
    username_or_email = st.text_input("Username or Email", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    user_data = load_user_data()

    if st.button("Login"):
        hashed_password = hash_password(password)
        for username, details in user_data.items():
            if (username_or_email == username or username_or_email == details["email"]) and hashed_password == details["password"]:
                st.success("Login successful!")
                st.session_state['username'] = username
                st.session_state['login_time'] = time.time()
                switch_page("dashboard")
                return
        st.error("Invalid username, email, or password.")


# Main logic
if "username" not in st.session_state:
    st.session_state["username"] = None

if st.session_state["username"] is None:
    option = st.sidebar.selectbox("Choose", ["Login", "Register"])
    if option == "Register":
        register()
    else:
        login()
else:
    st.write(f"Welcome, {st.session_state['username']}!")
    st.button("Logout", on_click=lambda: st.session_state.clear())