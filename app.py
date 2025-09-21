# ================================
# GreenHerbs Traceability System
# ================================

import streamlit as st
import datetime
import random
import pandas as pd
import folium
from streamlit_folium import st_folium
import qrcode
from io import BytesIO
from math import radians, sin, cos, sqrt, atan2
from geopy.distance import geodesic
import plotly.express as px

# -------------------------------
# Streamlit Page Config
# -------------------------------
st.set_page_config(
    page_title="🌱 GreenHerbs Traceability",
    page_icon="🌿",
    layout="wide"
)

st.title("🌱 GreenHerbs Traceability System")

# -------------------------------
# Custom CSS Styling
# -------------------------------
st.markdown("""
<style>
    body { background-color: #f7f9fa; }
    .main > div { padding: 1.5rem; }
    h1, h2, h3, h4 { font-family: 'Segoe UI', sans-serif; font-weight: 600; }
    .stButton>button {
        background-color: #2e7d32; color: white; font-weight: bold;
        border-radius: 10px; padding: 0.6rem 1.2rem; border: none;
        box-shadow: 0px 4px 8px rgba(46,125,50,0.3);
    }
    .stButton>button:hover {
        background-color: #1b5e20; color: #e8f5e9;
    }
    .card {
        background-color: #808080;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.1);
    }
    .status-ok { color: green; font-weight: bold; }
    .status-bad { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Session State
# -------------------------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = []
if "batches" not in st.session_state:
    st.session_state.batches = {}
if "recalls" not in st.session_state:
    st.session_state.recalls = set()

# -------------------------------
# Blockchain Function
# -------------------------------
def add_block(data):
    block = {
        "index": len(st.session_state.blockchain)+1,
        "timestamp": str(datetime.datetime.now()),
        "data": data
    }
    st.session_state.blockchain.append(block)

# -------------------------------
# ESP Sensor Simulation
# -------------------------------
def simulate_esp8266():
    return {"temperature": round(random.uniform(25,40),2), "humidity": round(random.uniform(40,80),2)}

# -------------------------------
# QR Code
# -------------------------------
def generate_qr(batch_id):
    qr = qrcode.make(f"http://localhost:8501/?batch={batch_id}&page=Journey")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

# -------------------------------
# Geo-Fencing
# -------------------------------
ALLOWED_ZONES = {
    "Ashwagandha": (24.47, 75.13),
    "Tulsi": (27.58, 77.70),
    "Brahmi": (9.49, 76.33),
    "Neem": (26.29, 73.02)
}
MAX_DISTANCE_KM = 200

def is_within_allowed(lat, lon, species):
    allowed_lat, allowed_lon = ALLOWED_ZONES[species]
    distance = geodesic((lat, lon), (allowed_lat, allowed_lon)).km
    return distance <= MAX_DISTANCE_KM, distance

# -------------------------------
# Batch Health Score
# -------------------------------
def calculate_health(batch):
    steps = len(batch['processing'])
    tests = len(batch['testing'])
    health = min(100, (steps/5)*60 + (tests/3)*40)  # weighted
    return int(health)

# -------------------------------
# Predictive Quality
# -------------------------------
def predict_quality(batch):
    criteria_passed = 0
    total_criteria = 5

    # Drying temp
    drying = [s for s in batch['processing'] if s['step'].lower()=="drying"]
    if drying and drying[0]['details'].get("temperature",100)<=40: criteria_passed+=1

    # Grinding speed
    grinding = [s for s in batch['processing'] if s['step'].lower()=="grinding"]
    if grinding and grinding[0]['details'].get("speed",5000)<=3000: criteria_passed+=1

    # Moisture
    moisture = [t for t in batch['testing'] if t['test'].lower()=="moisture content"]
    if moisture and moisture[0]['details'].get("percentage",100)<=12: criteria_passed+=1

    # Microbial load
    microbial = [t for t in batch['testing'] if t['test'].lower()=="microbial load"]
    if microbial and microbial[0]['details'].get("cfu",100000)<=500: criteria_passed+=1

    # Heavy metals
    heavy = [t for t in batch['testing'] if t['test'].lower()=="heavy metals"]
    if heavy and heavy[0]['details'].get("lead_ppm",10)<=0.5: criteria_passed+=1

    return round((criteria_passed/total_criteria)*100,1)

# ================================
# PAGES
# ================================

# --- Dashboard ---
def render_dashboard():
    st.subheader("📊 Dashboard Overview")
    if not st.session_state.batches:
        st.info("No batches yet.")
        return

    species_filter = st.multiselect("Filter Species", list(ALLOWED_ZONES.keys()), default=list(ALLOWED_ZONES.keys()))
    status_filter = st.multiselect("Filter Status", ["Active","Recalled"], default=["Active","Recalled"])

    summary = []
    for batch_id, data in st.session_state.batches.items():
        status = "Recalled" if batch_id in st.session_state.recalls else "Active"
        if data['species'] in species_filter and status in status_filter:
            summary.append({
                "batch_id": batch_id,
                "species": data['species'],
                "steps_completed": len(data['processing']),
                "tests_done": len(data['testing']),
                "status": status
            })
    if not summary:
        st.info("No batches match filter")
        return

    df = pd.DataFrame(summary)

    for _, row in df.iterrows():
        status_class = "status-bad" if row['status']=="Recalled" else "status-ok"
        st.markdown(f"<div class='card'><h3>{row['batch_id']} - {row['species']} <span class='{status_class}'>[{row['status']}]</span></h3><p>Steps: {row['steps_completed']}</p><p>Tests: {row['tests_done']}</p></div>", unsafe_allow_html=True)
        st.image(generate_qr(row['batch_id']), width=120)

    # Charts
    fig1 = px.pie(df, names='status', title="Batch Status Distribution")
    st.plotly_chart(fig1, use_container_width=True)

# --- Collection ---
def render_collection_form():
    st.subheader("🌿 Add Collection")
    species = st.selectbox("Species", list(ALLOWED_ZONES.keys()))
    default_lat, default_lon = ALLOWED_ZONES[species]

    if "lat" not in st.session_state: st.session_state.lat = default_lat
    if "lon" not in st.session_state: st.session_state.lon = default_lon

    if st.button("📍 Fetch My Location"):
        st.session_state.lat = default_lat
        st.session_state.lon = default_lon
        st.info("Device location fetched (simulated)")

    lat = st.number_input("Latitude", -90.0, 90.0, float(st.session_state.lat))
    lon = st.number_input("Longitude", -180.0, 180.0, float(st.session_state.lon))
    collector = st.text_input("Collector Name")

    is_approved, distance = is_within_allowed(lat, lon, species)
    if is_approved: st.success(f"✅ Location OK ({distance:.1f} km from zone)")
    else: st.error(f"❌ Not in approved zone ({distance:.1f} km away)")

    with st.form("collection_form"):
        submitted = st.form_submit_button("Add Collection")
        if submitted and is_approved:
            batch_id = f"{species[:3].upper()}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            st.session_state.batches[batch_id] = {
                "species": species,
                "location": (lat, lon),
                "collector": collector,
                "timestamp": str(datetime.datetime.now()),
                "processing": [],
                "testing": []
            }
            add_block({"action":"collection","batch_id":batch_id,"species":species})
            st.success(f"Batch {batch_id} added!")

# --- Processing ---
def render_processing():
    st.subheader("⚙️ Processing Steps")
    if not st.session_state.batches: st.info("No batches found"); return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))
    batch = st.session_state.batches[batch_id]

    if st.button("Fetch ESP Data"):
        data = simulate_esp8266()
        st.info(f"Temp: {data['temperature']}°C | Humidity: {data['humidity']}%")

    step_options = ["Drying","Cleaning","Grinding","Powdering","Packaging"]
    step = st.selectbox("Step", step_options)
    details = {}
    if step=="Drying":
        details["duration"]=st.number_input("Duration (hrs)",1,48)
        details["temperature"]=st.number_input("Temperature (°C)",20,100)
    elif step=="Grinding":
        details["duration"]=st.number_input("Time (mins)",1,120)
        details["speed"]=st.number_input("Speed (RPM)",100,5000)
        details["fineness"]=st.selectbox("Fineness",["Coarse","Medium","Fine"])
    elif step=="Powdering":
        details["mesh_size"]=st.selectbox("Mesh Size",["60","100","200"])
    elif step=="Packaging":
        details["material"]=st.selectbox("Material",["Plastic","Paper","Eco-friendly"])
        details["seal"]=st.selectbox("Seal",["Standard","Tamper-proof","Authentic Seal"])

    with st.form("proc_form"):
        submitted=st.form_submit_button("Add Step")
        if submitted:
            batch["processing"].append({"step":step,"details":details,"timestamp":str(datetime.datetime.now())})
            add_block({"action":"processing","batch_id":batch_id,"step":step,"details":details})
            st.success(f"{step} added to {batch_id}")

# --- Quality Testing ---
def render_quality_testing():
    st.subheader("🧪 Quality Testing")
    if not st.session_state.batches: st.info("No batches"); return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))
    batch = st.session_state.batches[batch_id]

    tests = ["Moisture Content","Microbial Load","Heavy Metals"]
    test = st.selectbox("Test Type", tests)
    details={}
    if test=="Moisture Content": details["percentage"]=st.slider("Moisture %",0.0,100.0,10.0)
    elif test=="Microbial Load": details["cfu"]=st.number_input("CFU/g",0,100000,100)
    elif test=="Heavy Metals": details["lead_ppm"]=st.number_input("Lead ppm",0.0,10.0,0.1)

    with st.form("test_form"):
        submitted=st.form_submit_button("Add Test")
        if submitted:
            batch["testing"].append({"test":test,"details":details,"timestamp":str(datetime.datetime.now())})
            add_block({"action":"testing","batch_id":batch_id,"test":test,"details":details})
            st.success(f"{test} added to {batch_id}")

# --- Recall ---
def render_recall():
    st.subheader("⚠️ Recall Product")
    if not st.session_state.batches: st.info("No batches"); return
    batch_id = st.selectbox("Select Batch to Recall", list(st.session_state.batches.keys()))
    with st.form("recall_form"):
        reason = st.text_area("Reason")
        submitted=st.form_submit_button("Recall Batch")
        if submitted:
            st.session_state.recalls.add(batch_id)
            add_block({"action":"recall","batch_id":batch_id,"reason":reason})
            st.success(f"Batch {batch_id} recalled!")

# --- Journey ---
def render_journey():
    st.subheader("🚚 Product Journey")
    if not st.session_state.batches: st.info("No batches"); return
    batch_id = st.selectbox("Select Batch", list(st.session_state.batches.keys()))
    batch = st.session_state.batches[batch_id]

    st.markdown(f"### {batch_id} - {batch['species']}")
    health_score = calculate_health(batch)
    st.markdown(f"**Batch Health Score:** {health_score}%")
    st.progress(health_score)
    predicted_quality = predict_quality(batch)
    st.markdown(f"**Predicted Quality:** {predicted_quality}%")

    if batch_id in st.session_state.recalls: st.error("⚠️ This batch has been recalled")
    else: st.success("✅ Batch is active")

    lat, lon = batch["location"]
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], popup=f"Batch: {batch_id}\nCollector: {batch['collector']}", tooltip="Harvest", icon=folium.Icon(color="green", icon="leaf")).add_to(m)

    for i, step in enumerate(batch["processing"], start=1):
        folium.Marker([lat+0.05*i, lon+0.05*i], popup=f"{step['step']} at {step['timestamp']} Details: {step['details']}", tooltip=step['step'], icon=folium.Icon(color="blue", icon="cogs")).add_to(m)
    for i, test in enumerate(batch["testing"], start=1):
        folium.Marker([lat-0.05*i, lon-0.05*i], popup=f"{test['test']} at {test['timestamp']} Details: {test['details']}", tooltip=test['test'], icon=folium.Icon(color="red", icon="flask")).add_to(m)

    st_folium(m, width=800, height=500)

    st.markdown("### 🔹 Processing Summary")
    if batch["processing"]:
        for s in batch["processing"]:
            st.markdown(f"- **{s['step']}** at {s['timestamp']}, Details: {s['details']}")
    else:
        st.info("No processing yet")

    st.markdown("### 🔹 Testing Summary")
    if batch["testing"]:
        for t in batch["testing"]:
            st.markdown(f"- **{t['test']}** at {t['timestamp']}, Details: {t['details']}")
    else:
        st.info("No testing yet")

    st.image(generate_qr(batch_id), width=150)

# --- Blockchain Explorer ---
def render_blockchain_explorer():
    st.subheader("🔗 Blockchain Explorer")
    if not st.session_state.blockchain:
        st.info("No blocks yet.")
        return
    for block in st.session_state.blockchain:
        with st.expander(f"Block {block['index']} | {block['timestamp']}"):
            st.json(block["data"])

# -------------------------------
# Sidebar Navigation
# -------------------------------
menu = st.sidebar.radio("Navigation", ["Dashboard","Add Collection","Processing","Quality Testing","Journey","Recall Product","Blockchain Explorer"])
st.sidebar.markdown("<br><br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown("**🌿 GreenHerbs v1.0**")
st.sidebar.markdown("Built for SIH 25 🔹 Team Defcon")

# -------------------------------
# Navigation Logic
# -------------------------------
if menu=="Dashboard": render_dashboard()
elif menu=="Add Collection": render_collection_form()
elif menu=="Processing": render_processing()
elif menu=="Quality Testing": render_quality_testing()
elif menu=="Journey": render_journey()
elif menu=="Recall Product": render_recall()
elif menu=="Blockchain Explorer": render_blockchain_explorer()
