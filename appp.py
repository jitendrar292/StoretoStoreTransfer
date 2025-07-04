import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime
import random

TRANSFER_FILE = "transfer_requests.csv"

users = {
    "storea@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store A"},
    "storeb@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store B"},
    "storec@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store C"},
    "approver@adidas.com": {"password": "approver123", "role": "Approver"}
}

# Session Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'user_store' not in st.session_state:
    st.session_state.user_store = None
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = pd.DataFrame()
if 'transfer_requests' not in st.session_state:
    if os.path.exists(TRANSFER_FILE):
        st.session_state.transfer_requests = pd.read_csv(TRANSFER_FILE).to_dict('records')
    else:
        st.session_state.transfer_requests = []

def save_transfer_requests():
    df = pd.DataFrame(st.session_state.transfer_requests)
    df.to_csv(TRANSFER_FILE, index=False)

def login():
    st.title("Adidas Store-to-Store Transfers")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(email)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user_store = user.get("store", None)
        else:
            st.error("Invalid credentials")

def sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg", width=100)
        st.markdown(f"**Role:** {st.session_state.role}")
        if st.session_state.user_store:
            st.markdown(f"**Store:** {st.session_state.user_store}")
        nav = st.radio("Navigate", [
            "Dashboard",
            "Upload Inventory",
            "Transfer Suggestions",
            "Submit Transfer",
            "Approvals",
            "Receive Inventory"
        ])
        if st.button("Logout 🔓"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return nav
def upload_inventory():
    st.subheader("Upload Inventory CSV")
    uploaded = st.file_uploader("Upload CSV with SKU, Product, Stock Qty, Store", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)

        # Simulate Sales Last Week per row
        df["Sales Last Week"] = [random.randint(5, 40) for _ in range(len(df))]
        st.session_state.inventory_data = df
        st.success("Inventory loaded with simulated sales data.")
        st.dataframe(df)

def dashboard():
    st.subheader("Dashboard")
    if st.session_state.inventory_data.empty:
        st.warning("Upload inventory data first.")
        return
    st.write("### Current Inventory")
    st.dataframe(st.session_state.inventory_data)

def transfer_suggestions():
    st.subheader("Smart Transfer Suggestions")

    df = st.session_state.inventory_data
    if df.empty:
        st.warning("Upload inventory data first.")
        return

    sku_groups = df.groupby("SKU")
    suggestions = []

    for sku, group in sku_groups:
        sorted_group = group.sort_values(by="Sales Last Week")
        if len(sorted_group) >= 2:
            from_store = sorted_group.iloc[0]
            to_store = sorted_group.iloc[-1]

            if from_store["Sales Last Week"] < to_store["Sales Last Week"]:
                qty = min(10, from_store["Stock Qty"])
                suggestions.append({
                    "SKU": sku,
                    "Product": from_store["Product"],
                    "From": from_store["Store"],
                    "To": to_store["Store"],
                    "Qty": qty,
                    "Submitted At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Status": "Suggested"
                })

    if suggestions:
        df_suggestions = pd.DataFrame(suggestions)
        st.dataframe(df_suggestions)

        for i, sug in enumerate(suggestions):
            if st.button(f"Submit Suggested Transfer {i+1}"):
                sug["Status"] = "Pending"
                st.session_state.transfer_requests.append(sug)
                save_transfer_requests()
                st.success(f"Transfer from {sug['From']} to {sug['To']} submitted.")
    else:
        st.info("No smart suggestions at the moment.")
def submit_transfer():
    st.subheader("Submit Manual Transfer")
    sku = st.text_input("SKU")
    qty = st.number_input("Qty", min_value=1)
    store_options = ["Store A", "Store B", "Store C"]
    from_loc = st.selectbox("From", store_options)
    to_loc = st.selectbox("To", store_options)

    if st.button("Submit Transfer"):
        st.session_state.transfer_requests.append({
            "SKU": sku,
            "Qty": qty,
            "From": from_loc,
            "To": to_loc,
            "Status": "Pending",
            "Product": "Manual Entry",
            "Submitted At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_transfer_requests()
        st.success("Manual transfer request submitted.")

def approvals():
    st.subheader("Approvals")

    df = pd.DataFrame([r for r in st.session_state.transfer_requests if r["Status"] in ["Pending"]])
    if df.empty:
        st.info("No pending approvals.")
        return

    for i, row in df.iterrows():
        with st.expander(f"{row['SKU']} - {row['Qty']} from {row['From']} to {row['To']}"):
            col1, col2 = st.columns(2)
            if col1.button(f"Approve {row['SKU']} [{i}]"):
                st.session_state.transfer_requests[i]["Status"] = "Approved"
                save_transfer_requests()
                st.success("Approved.")
                st.rerun()
            if col2.button(f"Deny {row['SKU']} [{i}]"):
                st.session_state.transfer_requests[i]["Status"] = "Denied"
                save_transfer_requests()
                st.error("Denied.")
                st.rerun()

def receive_inventory():
    st.subheader("Receive Inventory")

    approved = [r for r in st.session_state.transfer_requests if r["Status"] == "Approved"]
    if not approved:
        st.info("No approved transfers available.")
        return

    df = pd.DataFrame(approved)
    st.dataframe(df)

    if st.button("Mark as Received"):
        for req in st.session_state.transfer_requests:
            if req["Status"] == "Approved":
                req["Status"] = "Received"
        save_transfer_requests()
        st.success("All approved transfers marked as received.")
        st.rerun()
# Main App Routing
if not st.session_state.logged_in:
    login()
else:
    page = sidebar()
    if page == "Dashboard":
        dashboard()
    elif page == "Upload Inventory":
        upload_inventory()
    elif page == "Transfer Suggestions":
        transfer_suggestions()
    elif page == "Submit Transfer":
        submit_transfer()
    elif page == "Approvals" and st.session_state.role == "Approver":
        approvals()
    elif page == "Receive Inventory":
        receive_inventory()
