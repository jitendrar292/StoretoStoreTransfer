import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

TRANSFER_FILE = "transfer_requests.csv"

# User setup
users = {
    "storea@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store A"},
    "storeb@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store B"},
    "storec@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store C"},
    "approver@adidas.com": {"password": "approver123", "role": "Approver"}
}

# Session init
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
if 'suggested_transfer' not in st.session_state:
    st.session_state.suggested_transfer = None

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
    st.subheader("Upload Inventory and Sales Data")

    inventory_file = st.file_uploader("Upload Inventory CSV", type="csv", key="inv")
    sales_file = st.file_uploader("Upload Sales CSV", type="csv", key="sales")

    if inventory_file and sales_file:
        inv_df = pd.read_csv(inventory_file)
        sales_df = pd.read_csv(sales_file)

        # Merge on Store + SKU
        merged_df = pd.merge(inv_df, sales_df, on=["Store", "SKU"], how="left")
        merged_df["Sales Last Week"].fillna(0, inplace=True)

        st.session_state.inventory_data = merged_df
        st.success("Inventory and sales data uploaded & merged successfully.")
        st.dataframe(merged_df)

def dashboard():
    st.subheader("Dashboard")
    if st.session_state.inventory_data.empty:
        st.warning("Upload inventory data first.")
        return
    st.write("### Inventory Overview")
    st.dataframe(st.session_state.inventory_data)

def transfer_suggestions():
    st.subheader("Smart Transfer Suggestions")

    df = st.session_state.inventory_data
    if df.empty:
        st.warning("Upload data first.")
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
        st.write("### Suggested Transfers")
        for i, row in df_suggestions.iterrows():
            st.markdown(f"**{row['SKU']}**: {row['Qty']} units from {row['From']} → {row['To']}")
            if st.button(f"Transfer {row['SKU']} to {row['To']}", key=row['SKU'] + str(i)):
                st.session_state.suggested_transfer = row.to_dict()
                st.query_params["page"] = "Submit Transfer"
                st.rerun()
    else:
        st.info("No smart suggestions available.")

def submit_transfer():
    st.subheader("Submit Transfer")

    suggested = st.session_state.get("suggested_transfer", None)

    sku = st.text_input("SKU", value=suggested["SKU"] if suggested else "")
    qty = st.number_input("Quantity", min_value=1, value=int(suggested["Qty"]) if suggested else 1)
    store_options = ["Store A", "Store B", "Store C"]
    from_loc = st.selectbox("From", store_options, index=store_options.index(suggested["From"]) if suggested else 0)
    to_loc = st.selectbox("To", store_options, index=store_options.index(suggested["To"]) if suggested else 1)

    if st.button("Submit Transfer"):
        st.session_state.transfer_requests.append({
            "SKU": sku,
            "Qty": qty,
            "From": from_loc,
            "To": to_loc,
            "Status": "Pending",
            "Product": suggested["Product"] if suggested else "Manual Entry",
            "Submitted At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_transfer_requests()
        st.session_state.pop("suggested_transfer", None)
        st.success(f"Transfer request for SKU {sku} submitted.")

def approvals():
    st.subheader("Transfer Approvals")
    df = pd.DataFrame([r for r in st.session_state.transfer_requests if r["Status"] == "Pending"])
    if df.empty:
        st.info("No pending approvals.")
        return

    for i, row in df.iterrows():
        with st.expander(f"{row['SKU']} - {row['Qty']} from {row['From']} to {row['To']}"):
            col1, col2 = st.columns(2)
            if col1.button(f"Approve {row['SKU']} [{i}]", key=f"appr_{i}"):
                st.session_state.transfer_requests[i]["Status"] = "Approved"
                save_transfer_requests()
                st.success("Approved.")
                st.rerun()
            if col2.button(f"Deny {row['SKU']} [{i}]", key=f"deny_{i}"):
                st.session_state.transfer_requests[i]["Status"] = "Denied"
                save_transfer_requests()
                st.error("Denied.")
                st.rerun()

def receive_inventory():
    st.subheader("Receive Inventory")
    approved = [r for r in st.session_state.transfer_requests if r["Status"] == "Approved"]
    if not approved:
        st.info("No approved transfers.")
        return

    df = pd.DataFrame(approved)
    st.dataframe(df)

    if st.button("Mark as Received"):
        for r in st.session_state.transfer_requests:
            if r["Status"] == "Approved":
                r["Status"] = "Received"
        save_transfer_requests()
        st.success("All approved transfers marked as received.")
        st.rerun()

# Main App Routing
if not st.session_state.logged_in:
    login()
else:
    page_query = st.query_params.get("page", [None])[0]
    page = sidebar() if not page_query else page_query

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

