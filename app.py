import streamlit as st
import pandas as pd
import altair as alt

# Sample roles and login credentials
users = {
    "manager@adidas.com": {"password": "manager123", "role": "Store Manager"},
    "approver@adidas.com": {"password": "approver123", "role": "Approver"}
}

# Session initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = pd.DataFrame()

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

# Sidebar navigation
def sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg", width=100)
        st.markdown(f"**Role:** {st.session_state.role}")
        return st.radio("Navigate", ["Dashboard", "Manage Inventory", "Submit Transfer", "Approvals", "Receive Inventory", "Upload CSV"])

# Dashboard
def dashboard():
    st.subheader("Dashboard")
    if st.session_state.inventory_data.empty:
        st.warning("Upload inventory data first.")
        return

    df = st.session_state.inventory_data
    st.write("### Inventory Summary")
    st.dataframe(df)

    # Chart
    chart = alt.Chart(df).mark_bar().encode(
        x='Product',
        y='Stock Qty',
        color='Status'
    ).properties(width=600)
    st.altair_chart(chart)

# Manage Inventory
def manage_inventory():
    st.subheader("Manage Inventory")
    if st.session_state.inventory_data.empty:
        st.warning("No inventory data loaded.")
        return
    st.dataframe(st.session_state.inventory_data)

# Submit Transfer
def submit_transfer():
    st.subheader("Submit Transfer Request")
    sku = st.text_input("SKU")
    qty = st.number_input("Quantity", min_value=1)
    from_loc = st.text_input("From Location")
    to_loc = st.text_input("To Location")
    if st.button("Submit"):
        st.success(f"Transfer of {qty} units from {from_loc} to {to_loc} submitted for SKU {sku}.")

# Approvals
def approvals():
    st.subheader("Transfer Approvals")
    st.write("Pending approvals would be listed here.")
    names = ["John Doe", "Jane Smith", "Mike Patel"]
    for name in names:
        st.write(f"**{name}** - Marketing")
        col1, col2 = st.columns(2)
        with col1:
            st.button(f"Approve {name}")
        with col2:
            st.button(f"Deny {name}")

# Receive Inventory
def receive_inventory():
    st.subheader("Receive Inventory")
    if st.session_state.inventory_data.empty:
        st.warning("No inventory data loaded.")
        return
    df = st.session_state.inventory_data
    st.dataframe(df)
    if st.button("Update Status"):
        st.success("Inventory status updated.")

# Upload CSV
def upload_csv():
    st.subheader("Upload Inventory CSV")
    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state.inventory_data = df
        st.success("Data loaded successfully.")
        st.dataframe(df)

# App routing
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
