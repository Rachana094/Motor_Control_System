"""
=============================================================================
  Industrial IoT Smart Motor Monitoring & Control Dashboard
  Streamlit + Plotly + Modbus TCP
=============================================================================

  Connects to the PLC Gateway (plc_gateway.py) over Modbus TCP
  and provides a live visual interface for:
    - Motor status monitoring (RUNNING / STOPPED / FAULTED)
    - Temperature, Current, and Speed gauges
    - Remote Start / Stop / Fault Reset controls
    - Fault injection for testing (simulate overheating / overload)
    - Real-time trend chart history

  Run:  streamlit run app.py
  PLC Gateway must be running on localhost:5020
"""

import time
import streamlit as st
import plotly.graph_objects as go
from pymodbus.client import ModbusTcpClient
from datetime import datetime

# ── Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="Motor Control - IIoT Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Industrial Look ───────────────────────────────────
st.markdown("""
<style>
    /* Dark industrial theme overrides */
    .stApp {
        background-color: #0e1117;
    }

    /* Status banner styles */
    .status-running {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #000;
        padding: 15px 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 3px;
        box-shadow: 0 0 30px rgba(0, 200, 83, 0.4);
        animation: pulse-green 2s infinite;
    }
    .status-stopped {
        background: linear-gradient(135deg, #424242, #616161);
        color: #fff;
        padding: 15px 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 3px;
    }
    .status-faulted {
        background: linear-gradient(135deg, #d50000, #ff1744);
        color: #fff;
        padding: 15px 25px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 3px;
        box-shadow: 0 0 30px rgba(213, 0, 0, 0.5);
        animation: pulse-red 1s infinite;
    }

    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 200, 83, 0.3); }
        50% { box-shadow: 0 0 40px rgba(0, 200, 83, 0.6); }
    }
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 20px rgba(213, 0, 0, 0.3); }
        50% { box-shadow: 0 0 50px rgba(213, 0, 0, 0.8); }
    }

    /* Metric card styling */
    .metric-card {
        background: #1a1d23;
        border: 1px solid #2d3139;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-label {
        color: #9e9e9e;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
    }

    /* Indicator lamp styles */
    .lamp-on-green {
        display: inline-block;
        width: 24px; height: 24px;
        border-radius: 50%;
        background: radial-gradient(circle, #69f0ae, #00c853);
        box-shadow: 0 0 12px #00c853;
        margin-right: 8px;
        vertical-align: middle;
    }
    .lamp-on-red {
        display: inline-block;
        width: 24px; height: 24px;
        border-radius: 50%;
        background: radial-gradient(circle, #ff5252, #d50000);
        box-shadow: 0 0 12px #d50000;
        margin-right: 8px;
        vertical-align: middle;
    }
    .lamp-off {
        display: inline-block;
        width: 24px; height: 24px;
        border-radius: 50%;
        background: #2d3139;
        border: 2px solid #424242;
        margin-right: 8px;
        vertical-align: middle;
    }

    /* Button styling */
    div.stButton > button {
        width: 100%;
        padding: 12px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        letter-spacing: 1px;
    }

    /* Header styling */
    .dashboard-header {
        text-align: center;
        padding: 10px 0 5px 0;
    }
    .dashboard-header h1 {
        color: #e0e0e0;
        font-size: 24px;
        font-weight: 300;
        letter-spacing: 4px;
        text-transform: uppercase;
    }
    .dashboard-header .subtitle {
        color: #757575;
        font-size: 12px;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)


# ── Modbus TCP Connection ────────────────────────────────────────────
@st.cache_resource
def get_modbus_client():
    """Create and return a persistent Modbus TCP client."""
    client = ModbusTcpClient("127.0.0.1", port=5020)
    client.connect()
    return client


def read_plc_data():
    """Read all PLC data over Modbus TCP."""
    client = get_modbus_client()

    try:
        if not client.connected:
            client.connect()

        di = client.read_discrete_inputs(0, 6)
        hr = client.read_holding_registers(0, 4)

        if di.isError() or hr.isError():
            return None

        return {
            "motor_run": di.bits[0],
            "run_lamp": di.bits[1],
            "fault_lamp": di.bits[2],
            "fault_lockout": di.bits[3],
            "overtemp": di.bits[4],
            "overload": di.bits[5],
            "temperature": hr.registers[0],
            "current": hr.registers[1] / 10.0,
            "speed": hr.registers[2],
            "runtime": hr.registers[3],
        }
    except Exception:
        return None


def send_command(coil_address, value):
    """Write a command to the PLC via Modbus TCP."""
    client = get_modbus_client()
    try:
        client.write_coil(coil_address, value)
    except Exception:
        st.error("Failed to send command to PLC!")


def create_gauge(value, title, min_val, max_val, unit, thresholds):
    """Create a beautiful Plotly gauge chart."""
    # Determine bar color based on thresholds
    if value >= thresholds[1]:
        bar_color = "#ff1744"  # Red (danger)
    elif value >= thresholds[0]:
        bar_color = "#ff9100"  # Orange (warning)
    else:
        bar_color = "#00e676"  # Green (normal)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": f" {unit}", "font": {"size": 28, "color": "#e0e0e0"}},
        title={"text": title, "font": {"size": 14, "color": "#9e9e9e"}},
        gauge={
            "axis": {
                "range": [min_val, max_val],
                "tickcolor": "#616161",
                "tickfont": {"color": "#9e9e9e", "size": 10},
            },
            "bar": {"color": bar_color, "thickness": 0.75},
            "bgcolor": "#1a1d23",
            "borderwidth": 2,
            "bordercolor": "#2d3139",
            "steps": [
                {"range": [min_val, thresholds[0]], "color": "#1b2e1b"},
                {"range": [thresholds[0], thresholds[1]], "color": "#2e2a1b"},
                {"range": [thresholds[1], max_val], "color": "#2e1b1b"},
            ],
            "threshold": {
                "line": {"color": "#ff1744", "width": 3},
                "thickness": 0.8,
                "value": thresholds[1],
            },
        },
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e0e0e0"},
    )
    return fig


# ── Initialize Session State for Trend Data ─────────────────────────
if "temp_history" not in st.session_state:
    st.session_state.temp_history = []
    st.session_state.current_history = []
    st.session_state.speed_history = []
    st.session_state.time_history = []


# ══════════════════════════════════════════════════════════════════════
#   DASHBOARD LAYOUT
# ══════════════════════════════════════════════════════════════════════

# ── Header ───────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>⚙️ Smart Motor Monitoring & Control</h1>
    <div class="subtitle">Industrial IoT Dashboard • Modbus TCP • Real-Time</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Read PLC Data ────────────────────────────────────────────────────
data = read_plc_data()

if data is None:
    st.error("⚠️ Cannot connect to PLC Gateway! Make sure `plc_gateway.py` is running on port 5020.")
    st.info("Run: `python D:\\Motor_Control_System\\gateway\\plc_gateway.py`")
    st.stop()

# ── Update Trend History ─────────────────────────────────────────────
now = datetime.now().strftime("%H:%M:%S")
st.session_state.temp_history.append(data["temperature"])
st.session_state.current_history.append(data["current"])
st.session_state.speed_history.append(data["speed"])
st.session_state.time_history.append(now)

# Keep only last 60 data points
MAX_POINTS = 60
for key in ["temp_history", "current_history", "speed_history", "time_history"]:
    if len(st.session_state[key]) > MAX_POINTS:
        st.session_state[key] = st.session_state[key][-MAX_POINTS:]


# ── Row 1: Motor Status Banner ──────────────────────────────────────
if data["fault_lockout"]:
    status_class = "status-faulted"
    status_text = "⛔ MOTOR FAULTED — SAFETY LOCKOUT ACTIVE"
elif data["motor_run"]:
    status_class = "status-running"
    status_text = "✅ MOTOR RUNNING"
else:
    status_class = "status-stopped"
    status_text = "⬜ MOTOR STOPPED"

st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)
st.markdown("")


# ── Row 2: Indicator Lamps + Key Metrics ─────────────────────────────
col_lamps, col_temp, col_current, col_speed, col_runtime = st.columns([1.2, 1, 1, 1, 1])

with col_lamps:
    st.markdown("##### 💡 Indicator Panel")

    run_lamp = '<span class="lamp-on-green"></span>' if data["run_lamp"] else '<span class="lamp-off"></span>'
    fault_lamp = '<span class="lamp-on-red"></span>' if data["fault_lamp"] else '<span class="lamp-off"></span>'

    st.markdown(f'{run_lamp} **RUN LAMP** {"🟢 ON" if data["run_lamp"] else "⚫ OFF"}', unsafe_allow_html=True)
    st.markdown(f'{fault_lamp} **FAULT LAMP** {"🔴 ON" if data["fault_lamp"] else "⚫ OFF"}', unsafe_allow_html=True)

    st.markdown("")
    if data["overtemp"]:
        st.markdown("🌡️ **OVERTEMP TRIP:** 🔴 ACTIVE")
    if data["overload"]:
        st.markdown("⚡ **OVERLOAD TRIP:** 🔴 ACTIVE")

with col_temp:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🌡️ Temperature</div>
        <div class="metric-value">{data['temperature']}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col_current:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⚡ Motor Current</div>
        <div class="metric-value">{data['current']:.1f} A</div>
    </div>
    """, unsafe_allow_html=True)

with col_speed:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🔄 Motor Speed</div>
        <div class="metric-value">{data['speed']} RPM</div>
    </div>
    """, unsafe_allow_html=True)

with col_runtime:
    mins = data["runtime"] // 60
    secs = data["runtime"] % 60
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⏱️ Run Time</div>
        <div class="metric-value">{mins}:{secs:02d}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Row 3: Gauges ────────────────────────────────────────────────────
st.markdown("")
col_g1, col_g2, col_g3 = st.columns(3)

with col_g1:
    fig_temp = create_gauge(
        value=data["temperature"],
        title="MOTOR TEMPERATURE",
        min_val=0, max_val=100,
        unit="°C",
        thresholds=[60, 80],
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_g2:
    fig_current = create_gauge(
        value=data["current"],
        title="MOTOR CURRENT",
        min_val=0, max_val=20,
        unit="A",
        thresholds=[12, 15],
    )
    st.plotly_chart(fig_current, use_container_width=True)

with col_g3:
    fig_speed = create_gauge(
        value=data["speed"],
        title="MOTOR SPEED",
        min_val=0, max_val=1800,
        unit="RPM",
        thresholds=[1200, 1600],
    )
    st.plotly_chart(fig_speed, use_container_width=True)


# ── Row 4: Control Panel ────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🎛️ Control Panel")

col_start, col_stop, col_reset, col_spacer = st.columns([1, 1, 1, 1])

with col_start:
    if st.button("🟢 START MOTOR", type="primary", use_container_width=True):
        send_command(0, True)  # START_PB
        st.toast("✅ START command sent!", icon="🟢")
        time.sleep(0.3)
        st.rerun()

with col_stop:
    if st.button("🔴 STOP MOTOR", type="secondary", use_container_width=True):
        send_command(1, True)   # STOP_PB
        time.sleep(0.3)
        send_command(1, False)  # Release STOP
        st.toast("⛔ STOP command sent!", icon="🔴")
        time.sleep(0.3)
        st.rerun()

with col_reset:
    if st.button("🔄 FAULT RESET", type="secondary", use_container_width=True):
        send_command(2, True)  # FAULT_RESET
        st.toast("🔄 Fault Reset sent!", icon="🔄")
        time.sleep(0.3)
        st.rerun()


# ── Row 5: Fault Injection (Testing) ────────────────────────────────
st.markdown("---")
st.markdown("### 🧪 Fault Injection (Testing)")
st.caption("Simulate hardware faults to test the protection system.")

col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

with col_f1:
    if st.button("🌡️ Trigger OVERTEMP", use_container_width=True):
        send_command(3, True)  # TEMP_SENSOR trip
        st.toast("🌡️ Thermal trip simulated!", icon="🔥")
        time.sleep(0.5)
        send_command(3, False)
        st.rerun()

with col_f2:
    if st.button("⚡ Trigger OVERLOAD", use_container_width=True):
        send_command(4, True)  # CURRENT_SENSOR trip
        st.toast("⚡ Overload trip simulated!", icon="⚡")
        time.sleep(0.5)
        send_command(4, False)
        st.rerun()


# ── Row 6: Trend Chart ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Real-Time Trends")

fig_trend = go.Figure()

fig_trend.add_trace(go.Scatter(
    x=st.session_state.time_history,
    y=st.session_state.temp_history,
    mode="lines",
    name="Temperature (°C)",
    line=dict(color="#ff9100", width=2),
))

fig_trend.add_trace(go.Scatter(
    x=st.session_state.time_history,
    y=st.session_state.current_history,
    mode="lines",
    name="Current (A)",
    line=dict(color="#448aff", width=2),
))

fig_trend.add_trace(go.Scatter(
    x=st.session_state.time_history,
    y=[s / 10 for s in st.session_state.speed_history],  # Scale RPM to fit
    mode="lines",
    name="Speed (x10 RPM)",
    line=dict(color="#69f0ae", width=2),
))

fig_trend.update_layout(
    height=300,
    margin=dict(l=40, r=20, t=20, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0e1117",
    font={"color": "#9e9e9e"},
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11),
    ),
    xaxis=dict(gridcolor="#1a1d23", showgrid=True),
    yaxis=dict(gridcolor="#1a1d23", showgrid=True),
)

st.plotly_chart(fig_trend, use_container_width=True)


# ── Sidebar: System Info ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ System Info")
    st.markdown("---")

    st.markdown(f"**PLC Gateway:** `localhost:5020`")
    st.markdown(f"**Protocol:** Modbus TCP")
    st.markdown(f"**Scan Rate:** 100ms (10 Hz)")
    st.markdown(f"**Last Update:** {now}")

    st.markdown("---")
    st.markdown("### 📋 I/O Map")
    st.markdown("""
    | Address | Variable |
    |---|---|
    | `%IX0.0` | START_PB |
    | `%IX0.1` | STOP_PB |
    | `%IX0.2` | FAULT_RESET |
    | `%IX0.3` | TEMP_SENSOR |
    | `%IX0.4` | CURRENT_SENSOR |
    | `%QX0.0` | MOTOR_RUN |
    | `%QX0.1` | RUN_LAMP |
    | `%QX0.2` | FAULT_LAMP |
    """)

    st.markdown("---")
    st.markdown("### 🏭 Project")
    st.markdown("""
    **Industrial IoT Smart Motor**
    **Monitoring & Control System**

    Final Year Project
    BIT Bangalore — E&TC 2027
    """)

    st.markdown("---")
    refresh = st.slider("Auto-refresh (sec)", 1, 10, 2)


# ── Auto-refresh ─────────────────────────────────────────────────────
time.sleep(refresh)
st.rerun()

