import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

# -------------------------------
# File to store persistent transfer requests
TRANSFER_FILE = "transfer_requests.csv"

# -------------------------------
# Sample user credentials
users = {
    "manager@adidas.com": {"password": "manager123", "role": "Store Manager"},
    "approver@adidas.com": {"password": "approver123", "role": "Approver"}
}

# -------------------------------
# Session Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = pd.DataFrame()
if 'transfer_requests' not in st.session_state:
    if os.path.exists(TRANSFER_FILE):
        st.session_state.transfer_requests = pd.read_csv(TRANSFER_FILE).to_dict('records')
    else:
        st.session_state.transfer_requests = []

# -------------------------------
# Helper to save transfer requests
def save_transfer_requests():
    df = pd.DataFrame(st.session_state.transfer_requests)
    df.to_csv(TRANSFER_FILE, index=False)

# -------------------------------
# Login screen
def login():
    st.title("Adidas Store-to-Store Transfers")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(email)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
        else:
            st.error("Invalid credentials")

# -------------------------------
# Sidebar Navigation
def sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg", width=100)
        st.markdown(f"**Role:** {st.session_state.role}")
        nav = st.radio("Navigate", [
            "Dashboard",
            "Manage Inventory",
            "Submit Transfer",
            "Approvals",
            "Receive Inventory",
            "Upload CSV"
        ])
        if st.button("Logout 🔓"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.rerun()
        return nav

# -------------------------------
# Dashboard
def dashboard():
    st.subheader("Dashboard")
    if st.session_state.inventory_data.empty:
        st.warning("Upload inventory data first.")
        return

    df = st.session_state.inventory_data
    st.write("### Inventory Summary")
    st.dataframe(df)

    chart = alt.Chart(df).mark_bar().encode(
        x='Product',
        y='Stock Qty',
        color='Status'
    ).properties(width=600)
    st.altair_chart(chart)

    if st.session_state.transfer_requests:
        st.write("### All Transfer Requests")
        df_requests = pd.DataFrame(st.session_state.transfer_requests)
        st.dataframe(df_requests)

# -------------------------------
# Manage Inventory
def manage_inventory():
    st.subheader("Manage Inventory")
    if st.session_state.inventory_data.empty:
        st.warning("No inventory data loaded.")
        return
    st.dataframe(st.session_state.inventory_data)

# -------------------------------
# Submit Transfer
def submit_transfer():
    st.subheader("Submit Transfer Request")

    sku = st.text_input("SKU")
    qty = st.number_input("Quantity", min_value=1)
    store_options = ["Store A", "Store B", "Store C"]
    from_loc = st.selectbox("From Location", store_options)
    to_loc = st.selectbox("To Location", store_options)

    if st.button("Submit"):
        request = {
            "SKU": sku,
            "Quantity": qty,
            "From": from_loc,
            "To": to_loc,
            "Status": "Pending",
            "Submitted At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.transfer_requests.append(request)
        save_transfer_requests()
        st.success(f"Transfer of {qty} units from {from_loc} to {to_loc} submitted for SKU {sku}.")

# -------------------------------
# Approvals
def approvals():
    st.subheader("Transfer Approvals")

    if not st.session_state.transfer_requests:
        st.info("No transfer requests found.")
        return

    df = pd.DataFrame([r for r in st.session_state.transfer_requests if r["Status"] != "Received"])

    # Pending Requests
    pending = df[df["Status"] == "Pending"]
    if not pending.empty:
        st.write("### ⏳ Pending Requests")
        for i, req in pending.iterrows():
            with st.expander(f"{req['SKU']} - {req['Quantity']} units from {req['From']} to {req['To']}"):
                st.write(f"**Submitted At:** {req['Submitted At']}")
                col1, col2 = st.columns(2)
                if col1.button(f"Approve Request {i+1}"):
                    st.session_state.transfer_requests[i]["Status"] = "Approved"
                    save_transfer_requests()
                    st.success(f"Request {i+1} approved.")
                    st.rerun()
                if col2.button(f"Deny Request {i+1}"):
                    st.session_state.transfer_requests[i]["Status"] = "Denied"
                    save_transfer_requests()
                    st.error(f"Request {i+1} denied.")
                    st.rerun()
    else:
        st.info("No pending requests.")

    # Approved Requests
    approved = df[df["Status"] == "Approved"]
    if not approved.empty:
        st.write("### ✅ Approved Requests")
        st.dataframe(approved)

    # Denied Requests
    denied = df[df["Status"] == "Denied"]
    if not denied.empty:
        st.write("### ❌ Denied Requests")
        st.dataframe(denied)

# -------------------------------
# Receive Inventory
def receive_inventory():
    st.subheader("Receive Inventory")

    # Filter only approved transfers
    approved_transfers = [req for req in st.session_state.transfer_requests if req["Status"] == "Approved"]

    if not approved_transfers:
        st.info("No approved transfers available for receiving.")
        return

    df = pd.DataFrame(approved_transfers)
    st.dataframe(df)

    if st.button("Mark as Received"):
        for req in st.session_state.transfer_requests:
            if req["Status"] == "Approved":
                req["Status"] = "Received"
        save_transfer_requests()
        st.success("Approved inventory marked as received.")
        st.rerun()

# -------------------------------
# Upload CSV
def upload_csv():
    st.subheader("Upload Inventory CSV")
    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state.inventory_data = df
        st.success("Data loaded successfully.")
        st.dataframe(df)

# -------------------------------
# Main Routing
if not st.session_state.logged_in:
    login()
else:
    page = sidebar()
    if page == "Dashboard":
        dashboard()
    elif page == "Manage Inventory":
        manage_inventory()
    elif page == "Submit Transfer":
        submit_transfer()
    elif page == "Approvals" and st.session_state.role == "Approver":
        approvals()
    elif page == "Receive Inventory":
        receive_inventory()
    elif page == "Upload CSV":
        upload_csv()
