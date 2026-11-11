# 🏭 Industrial IoT-Based Smart Motor Monitoring & Control System

> **Final-Year Engineering Project (2027)**  
> **Student:** Rachana  
> **Institution:** Bangalore Institute of Technology (BIT Bangalore)  
> **Department:** Electronics & Telecommunication Engineering (E&TC)  
> **Target Industries:** ABB, Siemens, Schneider Electric, Rockwell Automation, Honeywell, Emerson  

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-00c853?style=for-the-badge&logo=streamlit&logoColor=white)](https://motorcontrolsystem-gxtrv7xzenwdwvh2k93lmx.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PLC Standard](https://img.shields.io/badge/Standard-IEC%2061131--3-orange?style=for-the-badge)](https://en.wikipedia.org/wiki/IEC_61131-3)
[![Protocol](https://img.shields.io/badge/Protocol-Modbus%20TCP-red?style=for-the-badge)](https://modbus.org/)

---

### 🌐 Live Interactive Cloud Application
👉 **Access the Live Industrial Dashboard:** **[https://motorcontrolsystem-gxtrv7xzenwdwvh2k93lmx.streamlit.app/](https://motorcontrolsystem-gxtrv7xzenwdwvh2k93lmx.streamlit.app/)**

---

## 📌 Project Overview

This project implements an end-to-end **Industry 4.0 Industrial IoT (IIoT)** system for remote condition monitoring, predictive maintenance, and fail-safe safety control of an industrial 3-phase induction motor.

It integrates:
1. **IEC 61131-3 Compliant Ladder Logic:** Designed and verified in OpenPLC Editor, featuring a 7-rung protection circuit with seal-in latching, thermal trip detection, overload protection, and latching safety lockouts.
2. **Modbus TCP Gateway Server:** Soft PLC runtime executing cyclic scan cycles (100 ms) and serving physical coils, discrete inputs, and holding registers.
3. **Real-Time Web HMI / IoT Dashboard:** Built with Streamlit and Plotly, delivering real-time condition gauges, alarm indicators, and remote operator controls.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STREAMLIT WEB HMI / IoT DASHBOARD                    │
│      • Real-Time Condition Gauges (Temperature, Current, Speed)       │
│      • Interactive Operator Controls (Start, Stop, Fault Reset)        │
│      • Live Predictive Telemetry Trend Charts                         │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Modbus TCP (Port 5020)
                                    │ Polling & Control Packets (10 Hz)
┌───────────────────────────────────▼────────────────────────────────────┐
│                    PLC MODBUS TCP GATEWAY ENGINE                       │
│     • Deterministic Cyclic Scan Engine (100 ms scan interval)          │
│     • Memory Register Mapper (Coils, Discrete Inputs, Holding Regs)   │
│     • High-Fidelity Physics-Based Motor Simulation Model              │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ IEC 61131-3 I/O Addressing
┌───────────────────────────────────▼────────────────────────────────────┐
│                  OPENPLC LADDER PROTECTION ENGINE                      │
│     • Rung 0: 3-Wire Seal-In Motor Starter with Safety Interlock       │
│     • Rung 1: Green Running Contactor Lamp                            │
│     • Rung 2: Motor Winding Thermal Trip Switch Detection              │
│     • Rung 3: Thermal Overload Relay Trip Detection                    │
│     • Rung 4: Red Warning Fault Lamp                                   │
│     • Rung 5: Set (S) Latch for Permanent Safety Lockout               │
│     • Rung 6: Reset (R) Unlatch for Safety Lockout via Fault Reset    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete IEC 61131-3 Memory Map & Modbus Table

| Variable | IEC Address | Modbus Type | Modbus Addr | Direction | Function in System |
|---|---|---|:---:|:---:|---|
| **`START_PB`** | `%IX0.0` | Coil | `0` | Input | Momentary Start Pushbutton (Normally Open) |
| **`STOP_PB`** | `%IX0.1` | Coil | `1` | Input | Momentary Stop Pushbutton (Normally Closed in logic) |
| **`FAULT_RESET`** | `%IX0.2` | Coil | `2` | Input | Fault Reset Pushbutton (Clears Safety Lockout) |
| **`TEMP_SENSOR`** | `%IX0.3` | Coil | `3` | Input | Motor Winding Thermal Switch Trip Contact |
| **`CURRENT_SENSOR`** | `%IX0.4` | Coil | `4` | Input | Bimetallic Overload Relay (TOR 95-96) Contact |
| **`MOTOR_RUN`** | `%QX0.0` | Discrete Input | `0` | Output | Main Contactor Coil (Drives 3-Phase Motor) |
| **`RUN_LAMP`** | `%QX0.1` | Discrete Input | `1` | Output | Green Indicator Pilot Light (Motor Running) |
| **`FAULT_LAMP`** | `%QX0.2` | Discrete Input | `2` | Output | Red Warning Pilot Light (Safety Lockout Active) |
| **`FAULT_LOCKOUT`** | Internal | Discrete Input | `3` | Internal | Safety Lockout Trip Latch (`SET` / `RESET`) |
| **`OVERTEMP_FAULT`** | Internal | Discrete Input | `4` | Internal | Thermal Trip Detected Flag |
| **`OVERLOAD_FAULT`** | Internal | Discrete Input | `5` | Internal | Overcurrent Trip Detected Flag |
| **`MOTOR_TEMP`** | `%IW0` | Holding Reg | `0` | Telemetry | Motor Winding Temperature in °C (Ambient: 25°C) |
| **`MOTOR_CURRENT`**| `%IW1` | Holding Reg | `1` | Telemetry | Motor Phase Current in 0.1 A units (e.g. 115 = 11.5 A) |
| **`MOTOR_SPEED`** | `%IW2` | Holding Reg | `2` | Telemetry | Motor Shaft Rotational Velocity in RPM (Nominal: 1500) |
| **`RUNTIME_SECS`** | `%IW3` | Holding Reg | `3` | Telemetry | Total Cumulative Motor Running Time (seconds) |

---

## 🪜 Complete Ladder Logic Breakdown (Rung by Rung)

Here is the exact ladder diagram logic running inside [`pous/programs/motor_ladder.ld`](pous/programs/motor_ladder.ld):

### 🟢 Rung 0: Motor Start/Stop Seal-In Circuit with Safety Interlock
```text
  |---[ START_PB ]--------[/ STOP_PB /]----[/ FAULT_LOCKOUT /]----( MOTOR_RUN )---|
  |        %IX0.0              %IX0.1              Internal           %QX0.0      |
  |                                                                               |
  |---[ MOTOR_RUN ]---|                                                           |
           %QX0.0                                                                 |
```
* **Boolean Logic Equation:**  
  $$\text{MOTOR\_RUN} := (\text{START\_PB} \lor \text{MOTOR\_RUN}) \land (\neg \text{STOP\_PB}) \land (\neg \text{FAULT\_LOCKOUT})$$
* **Operation & Output:**
  - Pressing `START_PB` pulses power to the `MOTOR_RUN` coil.
  - The parallel auxiliary contact `MOTOR_RUN` establishes a **seal-in (latch)** branch so the motor continues running when `START_PB` is released.
  - Pressing `STOP_PB` (negated contact) opens the circuit, immediately de-energizing `MOTOR_RUN`.
  - The normally closed contact `[/ FAULT_LOCKOUT /]` acts as the **safety interlock**: if any fault condition trips, this contact opens instantly to kill motor power.

---

### 💡 Rung 1: Green Run Pilot Lamp
```text
  |---[ MOTOR_RUN ]------------------------------------------------( RUN_LAMP )---|
           %QX0.0                                                      %QX0.1     |
```
* **Boolean Logic Equation:**  
  $$\text{RUN\_LAMP} := \text{MOTOR\_RUN}$$
* **Operation & Output:**  
  Whenever the main motor contactor is energized, the green panel indicator light turns ON to signal safe normal operation.

---

### 🔥 Rung 2: Motor Winding Thermal Trip Detection
```text
  |---[ TEMP_SENSOR ]----------------------------------------( OVERTEMP_FAULT )---|
           %IX0.3                                                      Internal   |
```
* **Boolean Logic Equation:**  
  $$\text{OVERTEMP\_FAULT} := \text{TEMP\_SENSOR}$$
* **Operation & Output:**  
  Monitors internal stator winding thermistors/PTC switches. When temperature exceeds safe operational thresholds (80°C), this input triggers the internal `OVERTEMP_FAULT` flag.

---

### ⚡ Rung 3: Thermal Overload Relay (TOR) Trip Detection
```text
  |---[ CURRENT_SENSOR ]-------------------------------------( OVERLOAD_FAULT )---|
           %IX0.4                                                      Internal   |
```
* **Boolean Logic Equation:**  
  $$\text{OVERLOAD\_FAULT} := \text{CURRENT\_SENSOR}$$
* **Operation & Output:**  
  Monitors the bimetallic thermal overload relay auxiliary contact (95-96). If prolonged overcurrent occurs (>15.0 A), this input triggers the internal `OVERLOAD_FAULT` flag.

---

### 🚨 Rung 4: Red Warning Fault Lamp
```text
  |---[ FAULT_LOCKOUT ]-------------------------------------------( FAULT_LAMP )---|
           Internal                                                    %QX0.2     |
```
* **Boolean Logic Equation:**  
  $$\text{FAULT\_LAMP} := \text{FAULT\_LOCKOUT}$$
* **Operation & Output:**  
  When the safety lockout latch is active, the red warning light illuminates to alert operators of an unaddressed trip condition.

---

### 🔒 Rung 5: Permanent Safety Lockout Latch (Set Coil)
```text
  |---[ OVERTEMP_FAULT ]----------------------------------------( S FAULT_LOCKOUT )|
  |        Internal                                                    Internal   |
  |                                                                               |
  |---[ OVERLOAD_FAULT ]---|                                                      |
           Internal                                                               |
```
* **Boolean Logic Equation:**  
  $$\text{IF } (\text{OVERTEMP\_FAULT} \lor \text{OVERLOAD\_FAULT}) \implies \text{SET}(\text{FAULT\_LOCKOUT})$$
* **Why a `SET ( S )` Coil is Used:**  
  With a standard non-latching coil, once an overheated motor cools down, the trip signal would clear and allow the motor to restart dangerously.  
  By using a **`SET` coil**, once a fault occurs, `FAULT_LOCKOUT` **permanently latches ON** and cannot turn off on its own, guaranteeing positive machinery lockout.

---

### 🔄 Rung 6: Safety Lockout Reset (Reset Coil)
```text
  |---[ FAULT_RESET ]-------------------------------------------( R FAULT_LOCKOUT )|
           %IX0.2                                                      Internal   |
```
* **Boolean Logic Equation:**  
  $$\text{IF } (\text{FAULT\_RESET}) \implies \text{RESET}(\text{FAULT\_LOCKOUT})$$
* **Operation & Output:**  
  The safety lockout can only be unlatched when an operator conducts inspection and presses the `FAULT_RESET` pushbutton (`%IX0.2`). This unlatches `FAULT_LOCKOUT`, restoring Rung 0 readiness.

---

## ⚡ Modbus TCP Protocol Configuration

Modbus TCP communicates over TCP port 502/5020 using standard industrial function codes:
* **Function Code 01 (Read Coils):** Reads momentary operator inputs (`START_PB`, `STOP_PB`, `FAULT_RESET`).
* **Function Code 02 (Read Discrete Inputs):** Reads output contactor and indicator lamp states (`MOTOR_RUN`, `RUN_LAMP`, `FAULT_LAMP`, `FAULT_LOCKOUT`).
* **Function Code 03 (Read Holding Registers):** Reads analog condition telemetry (Winding Temperature in °C, Phase Current in 0.1 A, Shaft RPM, Runtime).
* **Function Code 05/15 (Write Single/Multiple Coils):** Sends operator commands from the web HMI to the PLC.

---

## 📊 Live Industrial IoT Dashboard Features

The web dashboard (`app.py`) provides:
1. **Dynamic Status Header:** Real-time operational banner glowing green (`MOTOR RUNNING`), red (`MOTOR FAULTED — SAFETY LOCKOUT ACTIVE`), or grey (`MOTOR STOPPED`).
2. **Industrial Gauges (Plotly):**
   - **Temperature Gauge:** 0–100°C with Normal (0–60°C), Warning (60–80°C), and Trip (>80°C) zones.
   - **Current Gauge:** 0–20 A with Rated (0–12 A), Warning (12–15 A), and Overload (>15 A) zones.
   - **Speed Gauge:** 0–1800 RPM with synchronous speed marker (1500 RPM).
3. **Interactive Operator Console:** Remote controls for Start, Stop, and Fault Reset.
4. **Safety Interlock Testing Console:** Fault injection buttons to simulate real-time thermal trips and overload conditions.
5. **Real-Time Historical Telemetry Charts:** 50-point rolling line charts tracking temperature rise, phase current, and shaft velocity.

---

## 🧪 Automated Test Suite (7 Verification Tests)

Run the verification test suite:
```bash
python gateway/test_gateway.py
```

| # | Test Scenario | Expected Behavior | Result |
|:---:|---|---|:---:|
| **1** | **Initial State** | Motor STOPPED, Speed=0 RPM, Temp=25°C, Current=0.0 A | ✅ PASSED |
| **2** | **Start Motor** | Coil 0 pulse → `MOTOR_RUN` latches ON, `RUN_LAMP` illuminates | ✅ PASSED |
| **3** | **Speed Ramp** | 3-second run: Speed accelerates to ~1200 RPM, Temp rises | ✅ PASSED |
| **4** | **Thermal Trip** | Coil 3 pulse → Motor instantly stops, `FAULT_LAMP` ON, Lockout ON | ✅ PASSED |
| **5** | **Blocked Restart** | Start command sent while locked out → **Motor REFUSES to start** | ✅ PASSED |
| **6** | **Fault Reset & Restart**| Coil 2 pulse → Lockout clears → Start command succeeds | ✅ PASSED |
| **7** | **Orderly Shutdown** | Coil 1 pulse → Motor de-energizes smoothly to idle | ✅ PASSED |

---

## 🚀 How to Run Locally

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Launch the Dashboard
```bash
python -m streamlit run app.py
```
*The embedded Modbus TCP gateway will automatically initialize in the background on `127.0.0.1:5020`.*
