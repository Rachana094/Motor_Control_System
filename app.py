"""
=============================================================================
  Industrial IoT Smart Motor Monitoring & Control Dashboard
  Streamlit + Plotly + IEC 61131-3 PLC Architecture
=============================================================================
"""

import time
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import plc_gateway

# Initialize embedded PLC Controller runtime (executes 100ms scan cycle in background)
plc = plc_gateway.get_plc()

# ── Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Motor IIoT Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Industrial Dark Theme ──────────────────────────────
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }

    .status-running {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #000;
        padding: 14px 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
        box-shadow: 0 0 25px rgba(0, 200, 83, 0.4);
    }
    .status-stopped {
        background: linear-gradient(135deg, #424242, #616161);
        color: #fff;
        padding: 14px 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
    }
    .status-faulted {
        background: linear-gradient(135deg, #d50000, #ff1744);
        color: #fff;
        padding: 14px 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
        box-shadow: 0 0 30px rgba(213, 0, 0, 0.6);
    }

    .metric-card {
        background: #1a1d23;
        border: 1px solid #2d3139;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-label {
        color: #9e9e9e;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
    }

    .lamp-on-green {
        display: inline-block;
        width: 20px; height: 20px;
        border-radius: 50%;
        background: radial-gradient(circle, #69f0ae, #00c853);
        box-shadow: 0 0 10px #00c853;
        margin-right: 8px;
        vertical-align: middle;
    }
    .lamp-on-red {
        display: inline-block;
        width: 20px; height: 20px;
        border-radius: 50%;
        background: radial-gradient(circle, #ff5252, #d50000);
        box-shadow: 0 0 10px #d50000;
        margin-right: 8px;
        vertical-align: middle;
    }
    .lamp-off {
        display: inline-block;
        width: 20px; height: 20px;
        border-radius: 50%;
        background: #2d3139;
        border: 2px solid #424242;
        margin-right: 8px;
        vertical-align: middle;
    }

    div.stButton > button {
        width: 100%;
        padding: 10px;
        font-size: 15px;
        font-weight: 700;
        border-radius: 8px;
        letter-spacing: 1px;
    }

    .dashboard-header {
        text-align: center;
        padding: 5px 0;
    }
    .dashboard-header h1 {
        color: #e0e0e0;
        font-size: 26px;
        font-weight: 400;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 0;
    }
    .dashboard-header .subtitle {
        color: #757575;
        font-size: 12px;
        letter-spacing: 2px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


def read_plc_data():
    """Reads snapshot directly from the PLC runtime engine."""
    return plc.get_snapshot()


def send_command(cmd, value):
    """Dispatches operator command to the PLC runtime."""
    if cmd == "start":
        plc.pulse_start()
    elif cmd == "stop":
        plc.pulse_stop()
        time.sleep(0.1)
        plc.release_stop()
    elif cmd == "reset":
        plc.pulse_reset()
    elif cmd == "overtemp":
        plc.trigger_overtemp(value)
    elif cmd == "overload":
        plc.trigger_overload(value)


def create_gauge(value, title, min_val, max_val, unit, thresholds):
    if value >= thresholds[1]:
        bar_color = "#ff1744"
    elif value >= thresholds[0]:
        bar_color = "#ff9100"
    else:
        bar_color = "#00e676"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": f" {unit}", "font": {"size": 26, "color": "#e0e0e0"}},
        title={"text": title, "font": {"size": 13, "color": "#9e9e9e"}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickcolor": "#616161"},
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
        height=210,
        margin=dict(l=15, r=15, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e0e0e0"},
    )
    return fig


# ── Trend History ─────────────────────────────────────────────────────
if "temp_history" not in st.session_state:
    st.session_state.temp_history = []
    st.session_state.current_history = []
    st.session_state.speed_history = []
    st.session_state.time_history = []


# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>⚙️ Smart Motor Monitoring & Control</h1>
    <div class="subtitle">Industrial IoT Dashboard • Modbus TCP Architecture • IEC 61131-3 Core</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

data = read_plc_data()

now = datetime.now().strftime("%H:%M:%S")
st.session_state.temp_history.append(data["temperature"])
st.session_state.current_history.append(data["current"])
st.session_state.speed_history.append(data["speed"])
st.session_state.time_history.append(now)

MAX_POINTS = 50
for key in ["temp_history", "current_history", "speed_history", "time_history"]:
    if len(st.session_state[key]) > MAX_POINTS:
        st.session_state[key] = st.session_state[key][-MAX_POINTS:]

# ── Status Banner ─────────────────────────────────────────────────────
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

# ── Indicator Panel & Metrics ─────────────────────────────────────────
col_lamps, col_temp, col_current, col_speed, col_runtime = st.columns([1.2, 1, 1, 1, 1])

with col_lamps:
    st.markdown("##### 💡 Indicators")
    run_lamp = '<span class="lamp-on-green"></span>' if data["run_lamp"] else '<span class="lamp-off"></span>'
    fault_lamp = '<span class="lamp-on-red"></span>' if data["fault_lamp"] else '<span class="lamp-off"></span>'
    st.markdown(f'{run_lamp} **RUN LAMP** {"🟢 ON" if data["run_lamp"] else "⚫ OFF"}', unsafe_allow_html=True)
    st.markdown(f'{fault_lamp} **FAULT LAMP** {"🔴 ON" if data["fault_lamp"] else "⚫ OFF"}', unsafe_allow_html=True)

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
        <div class="metric-label">⚡ Current</div>
        <div class="metric-value">{data['current']:.1f} A</div>
    </div>
    """, unsafe_allow_html=True)

with col_speed:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🔄 Speed</div>
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

# ── Gauges ────────────────────────────────────────────────────────────
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

# ── Controls ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🎛️ Operator Control Panel")

c_start, c_stop, c_reset = st.columns(3)

with c_start:
    if st.button("🟢 START MOTOR (%IX0.0)", type="primary", use_container_width=True):
        send_command("start", True)
        st.toast("✅ START command pulsed!", icon="🟢")
        time.sleep(0.2)
        st.rerun()

with c_stop:
    if st.button("🔴 STOP MOTOR (%IX0.1)", type="secondary", use_container_width=True):
        send_command("stop", True)
        st.toast("⛔ STOP command sent!", icon="🔴")
        time.sleep(0.2)
        st.rerun()

with c_reset:
    if st.button("🔄 FAULT RESET (%IX0.2)", type="secondary", use_container_width=True):
        send_command("reset", True)
        st.toast("🔄 Reset signal sent!", icon="🔄")
        time.sleep(0.2)
        st.rerun()

# ── Fault Injection ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🧪 Safety Interlock Testing (Fault Injection)")
st.caption("Simulate hardware faults to test the PLC latching safety lockout.")

c_f1, c_f2 = st.columns(2)

with c_f1:
    if st.button("🔥 Simulate Overheat Trip (%IX0.3)", use_container_width=True):
        send_command("overtemp", True)
        st.toast("🔥 Thermal trip simulated!", icon="🔥")
        time.sleep(0.3)
        send_command("overtemp", False)
        st.rerun()

with c_f2:
    if st.button("⚡ Simulate Overload Relay Trip (%IX0.4)", use_container_width=True):
        send_command("overload", True)
        st.toast("⚡ Overload trip simulated!", icon="⚡")
        time.sleep(0.3)
        send_command("overload", False)
        st.rerun()

# ── Trend Chart ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Real-Time Condition Monitoring Trend")

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
    y=[s / 10 for s in st.session_state.speed_history],
    mode="lines",
    name="Speed (x10 RPM)",
    line=dict(color="#69f0ae", width=2),
))
fig_trend.update_layout(
    height=260,
    margin=dict(l=30, r=20, t=10, b=30),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0e1117",
    font={"color": "#9e9e9e"},
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(gridcolor="#1a1d23"),
    yaxis=dict(gridcolor="#1a1d23"),
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ System Architecture")
    st.markdown("---")
    st.markdown("**Protocol:** Modbus TCP & IEC 61131-3")
    st.markdown("**Engine:** Deterministic PLC Scan Loop")
    st.markdown("**Scan Interval:** 100ms (10 Hz)")
    st.markdown(f"**Last Sync:** {now}")

    st.markdown("---")
    st.markdown("### 📋 IEC 61131-3 Memory Map")
    st.markdown("""
    | Address | Variable | Type |
    |---|---|---|
    | `%IX0.0` | START_PB | Digital Input |
    | `%IX0.1` | STOP_PB | Digital Input |
    | `%IX0.2` | FAULT_RESET | Digital Input |
    | `%IX0.3` | TEMP_SENSOR | Digital Input |
    | `%IX0.4` | CURRENT_SENSOR | Digital Input |
    | `%QX0.0` | MOTOR_RUN | Digital Output |
    | `%QX0.1` | RUN_LAMP | Digital Output |
    | `%QX0.2` | FAULT_LAMP | Digital Output |
    """)

    st.markdown("---")
    st.markdown("### 🎓 Academic Project")
    st.markdown("""
    **Industrial IoT Smart Motor Monitoring & Control System**  
    Final Year Project (2027)  
    Department of E&TC, BIT Bangalore  
    """)

    refresh_rate = st.slider("Auto-refresh (sec)", 1, 5, 2)

time.sleep(refresh_rate)
st.rerun()
