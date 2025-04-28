# app.py
import streamlit as st
from reservation_agent import ReservationAgent

st.set_page_config(page_title="FoodieSpot Reservations")
agent = ReservationAgent()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("🍽️ FoodieSpot Reservation Assistant")

with st.form('input_form', clear_on_submit=True):
    user_input = st.text_input('Ask me to book, modify, or cancel a reservation')
    submitted = st.form_submit_button('Send')

if submitted and user_input:
    st.session_state.chat_history.append(("You", user_input))
    response = agent.handle(user_input)
    st.session_state.chat_history.append(("Assistant", response))

for sender, msg in st.session_state.chat_history:
    st.markdown(f"**{sender}:** {msg}")