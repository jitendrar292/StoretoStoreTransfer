import streamlit as st
import pandas as pd
import time
import base64
from pathlib import Path

# Set up the app
st.set_page_config(page_title="Adidas S2S", layout="wide")

# Load and encode logo image
def get_base64_logo(img_path):
    with open(img_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64_logo("Adidas_Logo.svg.png")  # Ensure this file is in the same folder

# --- Adidas Logo and Title ---
st.markdown(
    f"""
    <div style="text-align:center;">
        <img src="data:image/png;base64,{logo_base64}" width="150"/>
        <h1 style="font-family:Arial, sans-serif; margin-top:10px;">Adidas - Store to Store Transfer Stock Consolidation</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Custom CSS ---
st.markdown("""
    <style>
        .stButton>button {
            border-radius: 8px;
            background-color: #000000;
            color: white;
            padding: 0.6em 1.2em;
            margin: 0.5em;
            font-weight: 600;
        }
        .stRadio > div {
            padding: 1em;
            border: 1px solid #eee;
            border-radius: 10px;
        }
        h1, h2, h3 {
            color: #000000;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .css-1d391kg {
            overflow-x: auto;
        }
        .stDataFrame {
            overflow-x: auto;
            width: 100% !important;
            word-break: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# --- Navigation logic ---
if "step" not in st.session_state:
    st.session_state.step = 1

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(1, st.session_state.step - 1)

# --- Step Pages ---
if st.session_state.step == 1:
    st.header(" Select Market & Upload Store Nos")
    market = st.selectbox("Select Market", ["Germany", "France", "UK"])
    store_file = st.file_uploader("Upload Store Numbers Excel", type=["xlsx"])
    if store_file:
        st.success("✅ Store file uploaded. Click Next to continue.")

elif st.session_state.step == 2:
    st.header("Store to Store Transfer Stock Consolidation Preloading")
    steps = [
        "Pulling Sales Data...",
        "Checking Store Capacity...",
        "Processing Sales Duration for Store-Style Ranking...",
        "Calculating Share of Business...",
        "Evaluating Discount Benchmark for Liquidation...",
        "Assessing Pivotal Size Availability...",
        "Validating Minimum Live Days...",
        "Calculating Transfer Cost...",
        "Optimizing...",
        "Generating Final Recommendations..."
    ]
    with st.spinner("🔄 Processing..."):
        for step in steps:
            st.markdown(f"🟢 {step}")
            time.sleep(0.8)
    st.success("✅ Processing Complete")

elif st.session_state.step == 3:
    st.header("Transfer Movement Summary")
    summary_data = {
        "From Store": ["Berlin FO", "Munich FO", "Nuremberg FO"],
        "Berlin FO": ["", 29, 33],
        "Munich FO": [40, "", 22],
        "Nuremberg FO": [23, 13, ""]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.set_index("From Store", inplace=True)
    st.dataframe(summary_df, use_container_width=True)

elif st.session_state.step == 4:
    st.header("Raw Transfer Data Stats")
    raw_data = {
        "Channel": ["FR"] * 5,
        "FROM STORE": ["MUNICH FO"] * 5,
        "TO STORE": ["BERLIN FO"] * 5,
        "Style": ["EG4089", "FW2545", "S24039", "FW2545", "FU9609"],
        "Parent Style": ["EG4089", "FW2545", "S24039", "FW2545", "FU9609"],
        "Style Desc": ["TENSAUR C", "LITE RACER 2.0 K", "TENSAUR K", "LITE RACER 2.0 K", "STAN SMITH"],
        "Brand": ["ADIDAS", "ADIDAS", "ADIDAS", "ADIDAS", "ADIDAS ORIGINALS"],
        "Sport": ["RUNNING", "RUNNING", "RUNNING", "RUNNING", "ORIGINALS"],
        "Gender": ["KIDS", "KIDS", "KIDS", "KIDS", "MEN"],
        "Season": ["SS21", "FW20", "SS21", "FW20", "FW20"],
        "Size": [1, 3, 4, 2, 9],
        "EAN Code": ["4062053369004", "4062059375788", "4064044530110", "4062059375740", "4060518457129"],
        "Pre Stock": [10, 12, 10, 3, 5],
        "Post Stock": [0, 5, 0, 0, 0],
        "Pull Back": [0, 0, 0, 0, 0]
    }
    raw_df = pd.DataFrame(raw_data)
    st.dataframe(raw_df, use_container_width=True)

elif st.session_state.step == 5:
    st.header("Health Improvement at Stores")
    health_data = {
        "Brand": ["ADIDAS"] * 13 + [" ", "ORIGINALS", " ", "", ""],
        "Sport": [
            "BASKETBALL", "CRICKET", "FIELD HOCKEY", "FOOTBALL/SOCCER", "HIKING", "INDOOR",
            "OUTDOOR", "RUNNING", "SKATEBOARDING", "SWIM", "TENNIS", "TRAIL RUNNING", "TRAINING",
            "Total", "ORIGINALS", "SKATEBOARDING", "Total", "Grand Total"
        ],
        "Pre S2S - Store Style Count": [40,4,7,185,21,3,34,1134,18,4,150,13,73,1686,347,4,351,2037],
        "Post S2S - Store Style Count": [50,4,7,182,21,3,32,1118,20,4,168,14,59,1682,415,4,419,2101],
        "Pre S2S Healthy Combinations": [26,2,4,108,16,1,11,670,11,0,83,11,51,994,181,0,181,1175],
        "Post S2S Healthy Combinations": [37,2,4,138,20,1,13,763,13,0,99,14,44,1148,248,0,248,1396],
        "Pre S2S - health%": ["65%","50%","57%","58%","76%","33%","32%","59%","61%","0%","55%","85%","70%","59%","52%","0%","52%","58%"],
        "Post S2S - health%": ["74%","50%","57%","76%","95%","33%","41%","68%","65%","0%","59%","100%","75%","68%","60%","0%","59%","66%"]
    }
    health_df = pd.DataFrame(health_data)
    st.dataframe(health_df,use_container_width=True)

elif st.session_state.step == 6:
    st.header("Accept Transfers")
    transfer_choice = st.radio("Do you want to accept the transfer recommendations?", ["Yes", "No"])
    if transfer_choice == "Yes":
        st.success("🚀 Initiating S2S Transfers...")
    else:
        st.warning("⚠️ Transfers not initiated. Please review data and retry.")

elif st.session_state.step == 7:
    st.header("Submit Transfer Request Form")
    transfer_request = pd.DataFrame([
        {"SKU": "EG4089", "From": "MUNICH FO", "To": "BERLIN FO", "Qty": 10},
        {"SKU": "FW2545", "From": "MUNICH FO", "To": "BERLIN FO", "Qty": 5}
    ])
    st.dataframe(transfer_request, use_container_width=True)
    if st.button("📤 Submit Transfer Request"):
        st.session_state.request_submitted = True
        st.success("✅ Transfer Request Submitted. Waiting for Approval...")

elif st.session_state.step == 8:
    st.header("Approver Screen")
    if st.session_state.get("request_submitted"):
        approval = st.radio("Approve the transfer?", ["Approve", "Reject"], key="approval_decision")
        if approval == "Approve":
            st.session_state.approval_status = "Approved"
            st.success("✅ Approved. Proceeding to Transfer Channel Selection")
        else:
            st.session_state.approval_status = "Rejected"
            st.error("❌ Transfer Rejected")
    else:
        st.warning("⚠️ No transfer request found. Please go to Step 7")

elif st.session_state.step == 9:
    st.header("Send Store to Store Transfer Recommendation")
    channel = st.radio("Select Transfer Channel", ["Fiori", "ALS", "Harmony"], key="selected_channel")
    if st.button("➡️ Proceed to App"):
        st.session_state.selected_channel_final = channel
        st.session_state.step += 1

elif st.session_state.step == 10:
    st.header("Redirecting...")
    channel = st.session_state.get("selected_channel_final", "")
    if channel:
        st.markdown(f"""
            <h3>🔗 Redirecting to <span style="color: #000;">{channel}</span> App...</h3>
            <p style="font-size: 18px;">Please wait while we open the appropriate interface.</p>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No channel selected. Please go back and select a channel.")

# --- Bottom Navigation ---
st.markdown("---")
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.button("⬅️ Previous", on_click=prev_step)
with col3:
    st.button("➡️ Next", on_click=next_step)
