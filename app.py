import sys
import asyncio

# On Windows, use the ProactorEventLoop which supports subprocesses.
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import requests  # To make HTTP requests

BACKEND_URL = "http://localhost:8000" 

st.set_page_config(page_title="Price Pursuit AI", layout="centered")

st.title("🏷️ Price Pursuit AI")
st.write("Hello! 👋 Enter a product name or a product category to get the price(s) on competitor websites.")

user_input = st.text_input("Enter request:")

if st.button("Get Result"):
    st.text("Searching now!")
    if user_input:
        try:
            payload = {"user_input": user_input}
            response = requests.post(f"{BACKEND_URL}/get_price", json=payload)
            response.raise_for_status()  

            result_data = response.json()
            st.subheader("💡 Price Information from Competitor Website")
            st.text(result_data["results"])
            st.success("✅ Thank you for using this chatbot!")

        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error communicating with the backend: {e}")
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred: {e}")
    else:
        st.warning("⚠️ Please enter a product name.")