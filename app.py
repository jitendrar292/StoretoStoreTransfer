import streamlit as st
import pandas as pd
import altair as alt
import os

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
        return st.radio("Navigate", [
            "Dashboard",
            "Manage Inventory",
            "Submit Transfer",
            "Approvals",
            "Receive Inventory",
            "Upload CSV"
        ])

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
        st.write("### Transfer Requests")
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
            "Status": "Pending"
        }
        st.session_state.transfer_requests.append(request)
        save_transfer_requests()
        st.success(f"Transfer of {qty} units from {from_loc} to {to_loc} submitted for SKU {sku}.")

# -------------------------------
# Approvals
def approvals():
    st.subheader("Transfer Approvals")

    if not st.session_state.transfer_requests:
        st.info("No pending approvals.")
        return

    for i, req in enumerate(st.session_state.transfer_requests):
        if req["Status"] == "Pending":
            with st.expander(f"Request {i+1}: {req['SKU']} - {req['Quantity']} units"):
                st.write(f"**SKU**: {req['SKU']}")
                st.write(f"**Quantity**: {req['Quantity']}")
                st.write(f"**From**: {req['From']}")
                st.write(f"**To**: {req['To']}")
                col1, col2 = st.columns(2)
                if col1.button(f"Approve Request {i+1}"):
                    st.session_state.transfer_requests[i]["Status"] = "Approved"
                    save_transfer_requests()
                    st.success(f"Request {i+1} approved.")
                if col2.button(f"Deny Request {i+1}"):
                    st.session_state.transfer_requests[i]["Status"] = "Denied"
                    save_transfer_requests()
                    st.error(f"Request {i+1} denied.")

# -------------------------------
# Receive Inventory
def receive_inventory():
    st.subheader("Receive Inventory")
    if st.session_state.inventory_data.empty:
        st.warning("No inventory data loaded.")
        return
    st.dataframe(st.session_state.inventory_data)
    if st.button("Update Status"):
        st.success("Inventory status updated.")

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
