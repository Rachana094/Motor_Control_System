# 🏭 Industrial IoT-Based Smart Motor Monitoring & Control System

> **Final-Year Engineering Project (2027)**  
> **Author:** Rachana  
> **Department:** Electronics & Telecommunication Engineering (E&TC), BIT Bangalore  
> **Target Domains:** Industrial Automation, PLC/SCADA, Industry 4.0, IIoT, Embedded Systems  

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?logo=python)](https://www.python.org/)
[![PLC Standard](https://img.shields.io/badge/Standard-IEC%2061131--3-orange)](https://en.wikipedia.org/wiki/IEC_61131-3)
[![Protocol](https://img.shields.io/badge/Protocol-Modbus%20TCP-red)](https://modbus.org/)
[![UI](https://img.shields.io/badge/Dashboard-Streamlit%20%2B%20Plotly-green?logo=streamlit)](https://streamlit.io/)

---

## 📌 Project Overview

This project implements a complete **Industry 4.0 Industrial IoT (IIoT)** solution for remote monitoring, condition-based predictive maintenance, and fail-safe safety control of a 3-phase induction motor.

It integrates:
1. **IEC 61131-3 Compliant Ladder Logic:** Built using OpenPLC Editor with 7 comprehensive rungs covering start/stop seal-in latching, thermal trip protection, overload relay detection, and latching safety lockouts.
2. **Modbus TCP Gateway Server:** Soft PLC runtime executing cyclic scan cycles (100 ms) and exposing live coils and holding registers.
3. **Real-Time Web HMI / IoT Dashboard:** Interactive telemetry dashboard developed with Streamlit and Plotly, providing live condition gauges, alarm indicators, and remote operator controls.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│               INDUSTRIAL IoT CLOUD DASHBOARD            │
│         (Streamlit + Plotly Real-Time Gauges)          │
└───────────────────────────▲────────────────────────────┘
                            │ Modbus TCP (Port 5020)
                            │ Read: %QX0.0..%QX0.2, %IW0..%IW1
                            │ Write: %IX0.0..%IX0.4
┌───────────────────────────▼────────────────────────────┐
│             PLC MODBUS TCP GATEWAY ENGINE              │
│            (100ms Deterministic Scan Cycle)            │
└───────────────────────────▲────────────────────────────┘
                            │ IEC 61131-3 Memory Map
┌───────────────────────────▼────────────────────────────┐
│            OPENPLC LADDER PROTECTION LOGIC             │
│   Rung 0: Start/Stop Seal-In Latch + Safety Lockout    │
│   Rung 1: Green Run Lamp Contactor Indicator           │
│   Rung 2: Motor Thermal Trip Switch Detection          │
│   Rung 3: Thermal Overload Relay Trip Detection        │
│   Rung 4: Red Warning Fault Lamp Indicator             │
│   Rung 5: Set (S) Fault Lockout Latch on Any Trip      │
│   Rung 6: Reset (R) Fault Lockout Unlatch              │
└────────────────────────────────────────────────────────┘
```

---

## 📋 Memory Map & I/O Table

| Variable | Address | Type | Direction | Description |
|---|---|---|---|---|
| `START_PB` | `%IX0.0` | `BOOL` | Input | Motor Start Pushbutton (Normally Open) |
| `STOP_PB` | `%IX0.1` | `BOOL` | Input | Motor Stop Pushbutton (Normally Closed in logic) |
| `FAULT_RESET` | `%IX0.2` | `BOOL` | Input | Safety Lockout Reset Pushbutton |
| `TEMP_SENSOR` | `%IX0.3` | `BOOL` | Input | Motor Winding Thermal Trip Switch |
| `CURRENT_SENSOR` | `%IX0.4` | `BOOL` | Input | Thermal Overload Relay (TOR 95-96) Contact |
| `FAULT_LOCKOUT` | Internal | `BOOL` | Memory Flag | Safety Trip Latch (`SET` / `RESET` Coils) |
| `OVERTEMP_FAULT` | Internal | `BOOL` | Memory Flag | Thermal trip detected flag |
| `OVERLOAD_FAULT` | Internal | `BOOL` | Memory Flag | Overcurrent trip detected flag |
| `MOTOR_RUN` | `%QX0.0` | `BOOL` | Output | Main Motor Contactor Output |
| `RUN_LAMP` | `%QX0.1` | `BOOL` | Output | Green Indicator Lamp (Motor Active) |
| `FAULT_LAMP` | `%QX0.2` | `BOOL` | Output | Red Indicator Lamp (Safety Lockout Active) |

---

## ⚡ Safety Lockout & Interlock Mechanism

In industrial motor control (MCC standards):
- When an overtemperature or overload condition occurs, the PLC activates a **Set `( S )` latch** on `FAULT_LOCKOUT`.
- The normally closed contact on Rung 0 immediately drops the `MOTOR_RUN` coil, safely isolating the motor.
- **Fail-Safe Guarantee:** Even if the temperature cools down and the sensor returns to normal, the motor **WILL NOT** restart automatically. An operator must physically inspect the machine and press `FAULT_RESET` before restart is permitted.

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/rachana-bit/Motor_Control_System.git
cd Motor_Control_System
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Dashboard
```bash
streamlit run app.py
```
*The embedded Modbus TCP engine will automatically start in the background on `127.0.0.1:5020`.*

---

## 🧪 Automated Test Verification

Run the automated Modbus TCP test suite:
```bash
python gateway/test_gateway.py
```

Results:
- ✅ **Test 1:** Initial Idle State Verification
- ✅ **Test 2:** Start Pushbutton & Seal-In Latch
- ✅ **Test 3:** 3-Second Speed Ramp & Telemetry Update
- ✅ **Test 4:** Thermal Trip Safety Lockout Trip
- ✅ **Test 5:** Blocked Restart While Lockout Active
- ✅ **Test 6:** Fault Reset & Restart Verification
- ✅ **Test 7:** Stop Pushbutton & Orderly Shutdown

---

## 🎯 Academic & Professional Applications
- **Industry 4.0 Condition Monitoring:** Real-time temperature and vibration/current monitoring to avoid motor burnouts.
- **Predictive Maintenance:** Early detection of bearing wear or thermal breakdown.
- **Remote Supervisory Control (SCADA/HMI):** Complete visibility over plant equipment from any network location.
