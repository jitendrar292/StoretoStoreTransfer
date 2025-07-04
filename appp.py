import streamlit as st
import pandas as pd
from datetime import datetime
import os

TRANSFER_FILE = "transfer_requests.csv"

# ------------------ USER SETUP ---------------------
users = {
    "storea@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store A"},
    "storeb@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store B"},
    "storec@adidas.com": {"password": "store123", "role": "Store Manager", "store": "Store C"},
    "approver@adidas.com": {"password": "approver123", "role": "Approver"}
}

# ------------------ SESSION INIT -------------------
for key, val in {
    "logged_in": False,
    "role": None,
    "user_store": None,
    "user_email": None,
    "inventory_data": pd.DataFrame(),
    "suggested_transfer": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "transfer_requests" not in st.session_state:
    if os.path.exists(TRANSFER_FILE):
        st.session_state.transfer_requests = pd.read_csv(TRANSFER_FILE).to_dict('records')
    else:
        st.session_state.transfer_requests = []

def save_transfer_requests():
    pd.DataFrame(st.session_state.transfer_requests).to_csv(TRANSFER_FILE, index=False)

# ------------------ LOGIN --------------------------
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
            st.session_state.user_email = email
            st.rerun()
        else:
            st.error("Invalid credentials")

# ------------------ SIDEBAR ------------------------
def sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg", width=100)
        st.markdown(f"**Logged in as:** `{st.session_state.user_email}`")
        if st.session_state.user_store:
            st.markdown(f"**Store:** {st.session_state.user_store}")
        st.markdown("---")
        nav = st.radio("Navigation", [
            "Dashboard", "Upload Inventory", "Transfer Suggestions", 
            "Submit Transfer", "Approvals", "Receive Inventory"
        ])
        if st.button("Logout 🔓"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        return nav

# ------------------ UPLOAD INVENTORY ----------------
def upload_inventory():
    st.subheader("Upload Inventory and Sales Data")
    inv_file = st.file_uploader("Inventory CSV", type="csv", key="inv")
    sales_file = st.file_uploader("Sales CSV", type="csv", key="sales")

    if inv_file and sales_file:
        inv_df = pd.read_csv(inv_file)
        sales_df = pd.read_csv(sales_file)
        merged = pd.merge(inv_df, sales_df, on=["Store", "SKU"], how="left")
        merged["Sales Last Week"].fillna(0, inplace=True)
        st.session_state.inventory_data = merged
        st.success("Data uploaded successfully.")
        st.dataframe(merged)

# ------------------ DASHBOARD ----------------------
def dashboard():
    st.subheader("Dashboard")
    df = st.session_state.inventory_data
    if df.empty:
        st.info("Upload inventory to see dashboard.")
    else:
        st.dataframe(df[df["Store"] == st.session_state.user_store])

# ------------------ TRANSFER SUGGESTIONS ------------
def transfer_suggestions():
    st.subheader("Smart Transfer Suggestions")
    df = st.session_state.inventory_data
    if df.empty:
        st.warning("Upload inventory first.")
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
        st.write("### Suggested Transfers")
        for row in suggestions:
            st.markdown(f"**{row['SKU']}**: Suggest transferring {row['Qty']} from {row['From']} → {row['To']}")
            if st.button(f"Submit {row['SKU']}", key=row['SKU'] + row['From']):
                st.session_state.suggested_transfer = row
                st.rerun()
    else:
        st.info("No suggestions found.")

# ------------------ SUBMIT TRANSFER -----------------
def submit_transfer():
    st.subheader("Submit Transfer")
    suggested = st.session_state.get("suggested_transfer")

    sku = st.text_input("SKU", value=suggested["SKU"] if suggested else "")
    qty = st.number_input("Qty", min_value=1, value=int(suggested["Qty"]) if suggested else 1)
    stores = ["Store A", "Store B", "Store C"]
    from_loc = st.selectbox("From Store", stores, index=stores.index(suggested["From"]) if suggested else 0)
    to_loc = st.selectbox("To Store", stores, index=stores.index(suggested["To"]) if suggested else 1)

    if st.button("Submit Transfer"):
        if sku and from_loc != to_loc:
            st.session_state.transfer_requests.append({
                "SKU": sku,
                "Qty": qty,
                "From": from_loc,
                "To": to_loc,
                "Status": "Pending",
                "Product": suggested["Product"] if suggested else "Manual",
                "Submitted At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Submitted By": st.session_state.user_email
            })
            save_transfer_requests()
            st.session_state.suggested_transfer = None
            st.success("Transfer submitted.")
        else:
            st.warning("Check SKU and From/To store selection.")

# ------------------ APPROVALS -----------------------
def approvals():
    st.subheader("Transfer Approvals")
    pending = [r for r in st.session_state.transfer_requests if r["Status"] == "Pending"]
    if not pending:
        st.info("No pending approvals.")
        return

    for i, row in enumerate(pending):
        with st.expander(f"{row['SKU']} - {row['Qty']} from {row['From']} to {row['To']}"):
            st.markdown(f"Submitted by: `{row.get('Submitted By', 'N/A')}`")
            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"approve_{i}"):
                row["Status"] = "Approved"
                save_transfer_requests()
                st.success("Approved")
                st.rerun()
            if col2.button("Deny", key=f"deny_{i}"):
                row["Status"] = "Denied"
                save_transfer_requests()
                st.error("Denied")
                st.rerun()

# ------------------ RECEIVE INVENTORY ---------------
def receive_inventory():
    st.subheader("Receive Inventory")
    approved = [r for r in st.session_state.transfer_requests 
                if r["Status"] == "Approved" and r["To"] == st.session_state.user_store]

    if not approved:
        st.info("No transfers to receive.")
        return

    st.dataframe(pd.DataFrame(approved))

    if st.button("Mark as Received"):
        if st.session_state.inventory_data.empty:
            st.session_state.inventory_data = pd.DataFrame(columns=["Store", "SKU", "Product", "Stock Qty", "Sales Last Week"])

        for r in approved:
            r["Status"] = "Received"
            match = (
                (st.session_state.inventory_data["Store"] == r["To"]) &
                (st.session_state.inventory_data["SKU"] == r["SKU"])
            )

            if match.any():
                st.session_state.inventory_data.loc[match, "Stock Qty"] += int(r["Qty"])
            else:
                new_row = {
                    "Store": r["To"],
                    "SKU": r["SKU"],
                    "Product": r["Product"],
                    "Stock Qty": int(r["Qty"]),
                    "Sales Last Week": 0
                }
                st.session_state.inventory_data = pd.concat([
                    st.session_state.inventory_data, pd.DataFrame([new_row])
                ], ignore_index=True)

        save_transfer_requests()
        st.success("Inventory updated for received items.")
        st.rerun()

# ------------------ APP ROUTING ---------------------
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
