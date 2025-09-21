import streamlit as st
import datetime
import random
import pandas as pd
import pydeck as pdk
import qrcode
from io import BytesIO

# -------------------------------
# Custom CSS Styling
# -------------------------------
st.markdown("""
    <style>
        body {
            background-color: #f7f9fa;
        }
        .main > div {
            padding: 1.5rem;
        }
        h1, h2, h3, h4 {
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
        }
        .stButton>button {
            background-color: #2e7d32;
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 0.6rem 1.2rem;
            border: none;
            box-shadow: 0px 4px 8px rgba(46,125,50,0.3);
        }
        .stButton>button:hover {
            background-color: #1b5e20;
            color: #e8f5e9;
        }
        .card {
            background-color: white;
            border-radius: 15px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
        }
        .status-ok {
            color: green;
            font-weight: bold;
        }
        .status-bad {
            color: red;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Blockchain Simulation
# -------------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = []
if "batches" not in st.session_state:
    st.session_state.batches = {}
if "recalls" not in st.session_state:
    st.session_state.recalls = set()

def add_block(data):
    block = {
        "index": len(st.session_state.blockchain) + 1,
        "timestamp": str(datetime.datetime.now()),
        "data": data
    }
    st.session_state.blockchain.append(block)

# -------------------------------
# IoT ESP8266 Simulation
# -------------------------------
def simulate_esp8266():
    return {
        "temperature": round(random.uniform(25, 40), 2),
        "humidity": round(random.uniform(40, 80), 2)
    }

# -------------------------------
# QR Code Generator
# -------------------------------
def generate_qr(batch_id):
    qr = qrcode.make(f"http://localhost:8501/?batch={batch_id}&page=Journey")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

# -------------------------------
# Pages
# -------------------------------
def render_dashboard():
    st.subheader("📊 Dashboard Overview")
    if not st.session_state.batches:
        st.info("No batches yet. Add a collection first.")
        return

    for batch_id, data in st.session_state.batches.items():
        recalled = batch_id in st.session_state.recalls
        status = f"<span class='status-bad'>⚠️ Recalled</span>" if recalled else f"<span class='status-ok'>✅ Active</span>"

        st.markdown(f"""
            <div class='card'>
                <h3>{batch_id} - {data['species']} {status}</h3>
                <p><b>Collector:</b> {data['collector']}</p>
                <p><b>Harvested:</b> {data['location']} at {data['timestamp']}</p>
                <p><b>Steps:</b> {len(data['processing'])} | <b>Tests:</b> {len(data['testing'])}</p>
            </div>
        """, unsafe_allow_html=True)
        st.image(generate_qr(batch_id), width=120)

def render_collection_form():
    st.subheader("🌿 Add Collection")
    with st.form("collection_form"):
        species = st.selectbox("Species", ["Ashwagandha", "Tulsi", "Brahmi", "Neem"])
        lat = st.number_input("Latitude", -90.0, 90.0, 28.61)
        lon = st.number_input("Longitude", -180.0, 180.0, 77.20)
        collector = st.text_input("Collector Name")
        submitted = st.form_submit_button("Add Collection")
        if submitted:
            batch_id = f"{species[:3].upper()}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            st.session_state.batches[batch_id] = {
                "species": species,
                "location": (lat, lon),
                "collector": collector,
                "timestamp": str(datetime.datetime.now()),
                "processing": [],
                "testing": []
            }
            add_block({"action": "collection", "batch_id": batch_id, "species": species})
            st.success(f"Batch {batch_id} added successfully!")

def render_processing():
    st.subheader("⚙️ Processing Steps")
    if not st.session_state.batches:
        st.info("No batches found. Add a collection first.")
        return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))

    if st.button("📡 ESP8266 Sensor Data"):
        data = simulate_esp8266()
        st.info(f"Temp: {data['temperature']} °C | Humidity: {data['humidity']} %")

    steps = ["Drying", "Cleaning", "Grinding", "Powdering", "Packaging"]
    step = st.selectbox("Step", steps)

    details = {}
    if step == "Drying":
        details["duration"] = st.number_input("Drying Duration (hrs)", 1, 48)
        details["temperature"] = st.number_input("Temperature (°C)", 20, 100)
    elif step == "Grinding":
        details["duration"] = st.number_input("Grinding Time (mins)", 1, 120)
        details["speed"] = st.number_input("Speed (RPM)", 100, 5000)
        details["fineness"] = st.selectbox("Fineness", ["Coarse", "Medium", "Fine"])
    elif step == "Powdering":
        details["mesh_size"] = st.selectbox("Mesh Size", ["60", "100", "200"])
    elif step == "Packaging":
        details["material"] = st.selectbox("Packaging Material", ["Plastic", "Paper", "Eco-friendly"])
        details["seal"] = st.selectbox("Seal Type", ["Standard", "Tamper-proof", "Authentic Seal"])

    with st.form("processing_form"):
        submitted = st.form_submit_button("Add Step")
        if submitted:
            st.session_state.batches[batch_id]["processing"].append({
                "step": step,
                "details": details,
                "timestamp": str(datetime.datetime.now())
            })
            add_block({"action": "processing", "batch_id": batch_id, "step": step, "details": details})
            st.success(f"Step '{step}' added to batch {batch_id}")

def render_quality_testing():
    st.subheader("🧪 Quality Testing")
    if not st.session_state.batches:
        st.info("No batches available.")
        return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))

    tests = ["Moisture Content", "Microbial Load", "Heavy Metals"]
    test = st.selectbox("Test Type", tests)

    details = {}
    if test == "Moisture Content":
        details["percentage"] = st.slider("Moisture (%)", 0.0, 100.0, 10.0)
    elif test == "Microbial Load":
        details["cfu"] = st.number_input("CFU/g", 0, 100000, 100)
    elif test == "Heavy Metals":
        details["lead_ppm"] = st.number_input("Lead (ppm)", 0.0, 10.0, 0.1)

    with st.form("testing_form"):
        submitted = st.form_submit_button("Add Test Result")
        if submitted:
            st.session_state.batches[batch_id]["testing"].append({
                "test": test,
                "details": details,
                "timestamp": str(datetime.datetime.now())
            })
            add_block({"action": "testing", "batch_id": batch_id, "test": test, "details": details})
            st.success(f"Test '{test}' added to batch {batch_id}")

def render_journey():
    st.subheader("🚚 Product Journey")
    if not st.session_state.batches:
        st.info("No batches found.")
        return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))

    batch = st.session_state.batches[batch_id]
    st.markdown(f"<div class='card'><h3>{batch_id} - {batch['species']}</h3></div>", unsafe_allow_html=True)

    lat, lon = batch["location"]
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=5),
        layers=[pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"lat": lat, "lon": lon}]),
                          get_position='[lon, lat]', get_radius=100000, get_color=[200, 30, 0])]
    ))

    st.markdown("#### Processing Steps")
    for step in batch["processing"]:
        st.markdown(f"<div class='card'>✅ {step['step']} at {step['timestamp']}<br>", unsafe_allow_html=True)
        st.json(step["details"])

    st.markdown("#### Quality Tests")
    for test in batch["testing"]:
        st.markdown(f"<div class='card'>🧪 {test['test']} at {test['timestamp']}<br>", unsafe_allow_html=True)
        st.json(test["details"])

    st.markdown("#### Recall Section")
    if batch_id in st.session_state.recalls:
        st.error("⚠️ This batch has been recalled due to spoilage/expiry")
    else:
        st.success("✅ This batch is active and safe")

    st.image(generate_qr(batch_id), caption="Scan to view journey", width=150)

def render_recall():
    st.subheader("⚠️ Recall Product")
    if not st.session_state.batches:
        st.info("No batches available.")
        return
    batch_id = st.selectbox("Select Batch to Recall", list(st.session_state.batches.keys()))
    with st.form("recall_form"):
        reason = st.text_area("Reason for Recall")
        submitted = st.form_submit_button("Recall Batch")
        if submitted:
            st.session_state.recalls.add(batch_id)
            add_block({"action": "recall", "batch_id": batch_id, "reason": reason})
            st.error(f"Batch {batch_id} recalled!")

def render_blockchain_explorer():
    st.subheader("🔗 Blockchain Explorer")
    if not st.session_state.blockchain:
        st.info("No blocks yet.")
        return
    for block in st.session_state.blockchain:
        with st.expander(f"Block {block['index']} | {block['timestamp']}"):
            st.json(block["data"])

# -------------------------------
# Main App
# -------------------------------
st.set_page_config(page_title="GreenLeaf Traceability", layout="wide")
st.title("🌱 GreenLeaf Traceability System")

menu = st.sidebar.radio("📌 Navigation", [
    "Dashboard", "Add Collection", "Processing", "Quality Testing",
    "Journey", "Recall Product", "Blockchain Explorer"
])

if menu == "Dashboard":
    render_dashboard()
elif menu == "Add Collection":
    render_collection_form()
elif menu == "Processing":
    render_processing()
elif menu == "Quality Testing":
    render_quality_testing()
elif menu == "Journey":
    render_journey()
elif menu == "Recall Product":
    render_recall()
elif menu == "Blockchain Explorer":
    render_blockchain_explorer()
