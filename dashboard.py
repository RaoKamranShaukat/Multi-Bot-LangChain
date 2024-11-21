import streamlit as st
import json
import time
import pickle

from streamlit_extras.switch_page_button import switch_page

CHATBOT_FILE = "chatbots.pkl"

hide_sidebar_style = """
    <style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)


def count_bots(file_path):
        with open(file_path, "rb") as file:
            chatbots = pickle.load(file)
        if isinstance(chatbots, dict):  # Assuming the data is stored as a dictionary
            bot_count = len(chatbots)
        return bot_count


# Load user data
def load_user_data():
    try:
        with open("../database.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Dashboard
if "username" in st.session_state and st.session_state["username"]:
    username = st.session_state["username"]
    user_data = load_user_data()

    # Session timeout (24 hours)
    if time.time() - st.session_state["login_time"] > 86400:
        st.error("Session expired. Please log in again.")
        st.session_state["username"] = None
        st.session_state["login_time"] = None
        st.stop()

    st.title(f"Welcome, {username}")
    st.write("Here is the summary of your chatbots:")

    bot_count = count_bots(CHATBOT_FILE)

    if bot_count > 0:
        st.metric("Total Chatbots", bot_count)
    else:
        st.write("No chatbots created yet.")
else:
    st.error("You are not logged in. Please log in to view this page.")
    st.stop()

if st.button("Go To Bots Page"):
    switch_page("myBot")