import sys
import asyncio

# On Windows, use the ProactorEventLoop which supports subprocesses.
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from main import get_product_price  # This function queries your backend using Playwright

st.set_page_config(page_title="Price Pursuit AI", layout="centered")

st.title("🏷️ Price Pursuit AI")
st.write("Hello! 👋 Enter a product name or a product category to get the price(s) on competitor websites.")

user_input = st.text_input("Enter request:")

if st.button("Get Result"):
    st.text("Searching now!")
    if user_input:
        # Call the backend function which uses Playwright to fetch price data.
        result = get_product_price(user_input)
        st.subheader("💡 Price Information from Competitior Website")
        st.text(result)
        st.success("✅ Thank you for using this chatbot!")
    else:
        st.warning("⚠️ Please enter a product name.")
