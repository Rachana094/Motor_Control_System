# 🏭 Industrial IoT-Based Smart Motor Monitoring & Control System

> **Final-Year Engineering Project (2027)**  
> **Student:** Rachana  
> **Institution:** Bangalore Institute of Technology (BIT Bangalore)  
> **Department:** Electronics & Telecommunication Engineering (E&TC)  
> **Target Industries:** ABB, Siemens, Schneider Electric, Rockwell Automation, Honeywell, Emerson  

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PLC Standard](https://img.shields.io/badge/Standard-IEC%2061131--3-orange)](https://en.wikipedia.org/wiki/IEC_61131-3)
[![Protocol](https://img.shields.io/badge/Protocol-Modbus%20TCP-red)](https://modbus.org/)
[![UI](https://img.shields.io/badge/Dashboard-Streamlit%20%2B%20Plotly-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Industry%204.0%20%2F%20IIoT-brightgreen)](#system-architecture)

---

## 📖 Executive Summary (The 30-Second Elevator Pitch)

> *"In this project, I developed an end-to-end **Industry 4.0 Smart Motor Monitoring and Control System**. I engineered an **IEC 61131-3 compliant Ladder Logic** protection program in OpenPLC with latching safety lockouts, integrated a deterministic **Modbus TCP Gateway Server** (100 ms cyclic scan rate), and designed a real-time **Industrial IoT Web HMI** using Streamlit and Plotly for predictive condition monitoring, telemetry trending, and fail-safe remote operator control."*

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

Here is the exact ladder diagram logic running inside [`motor_ladder.ld`](file:///D:/Motor_Control_System/pous/programs/motor_ladder.ld):

### 🟢 Rung 0: Motor Start/Stop Seal-In Circuit with Safety Interlock
```text
  |---[ START_PB ]--------[/ STOP_PB /]----[/ FAULT_LOCKOUT /]----( MOTOR_RUN )---|
  |        %IX0.0              %IX0.1              Internal           %QX0.0      |
  |                                                                               |
  |---[ MOTOR_RUN ]---|                                                           |
           %QX0.0                                                                 |
```
* **Boolean Equation:**  
  $$\text{MOTOR\_RUN} := (\text{START\_PB} \lor \text{MOTOR\_RUN}) \land (\neg \text{STOP\_PB}) \land (\neg \text{FAULT\_LOCKOUT})$$
* **How It Works:**
  - Pressing `START_PB` energizes the `MOTOR_RUN` coil.
  - The parallel auxiliary contact `MOTOR_RUN` creates a **seal-in (latch)** branch so the motor keeps spinning even after `START_PB` is released.
  - Pressing `STOP_PB` (negated contact) breaks the power flow, de-energizing `MOTOR_RUN`.
  - The normally closed contact `[/ FAULT_LOCKOUT /]` is the **hardware safety interlock**: if any fault trips the system, this contact opens immediately, killing motor power instantly.

---

### 💡 Rung 1: Green Run Pilot Lamp
```text
  |---[ MOTOR_RUN ]------------------------------------------------( RUN_LAMP )---|
           %QX0.0                                                      %QX0.1     |
```
* **Boolean Equation:**  
  $$\text{RUN\_LAMP} := \text{MOTOR\_RUN}$$
* **How It Works:**  
  Whenever the motor contactor is energized, the green panel lamp illuminates to inform plant operators that the machine is live.

---

### 🔥 Rung 2: Motor Winding Thermal Trip Detection
```text
  |---[ TEMP_SENSOR ]----------------------------------------( OVERTEMP_FAULT )---|
           %IX0.3                                                      Internal   |
```
* **Boolean Equation:**  
  $$\text{OVERTEMP\_FAULT} := \text{TEMP\_SENSOR}$$
* **How It Works:**  
  In industrial motors, embedded PTC thermistors or bimetallic thermal switches trip when winding temperature exceeds 80°C. This activates the internal `OVERTEMP_FAULT` flag.

---

### ⚡ Rung 3: Thermal Overload Relay (TOR) Trip Detection
```text
  |---[ CURRENT_SENSOR ]-------------------------------------( OVERLOAD_FAULT )---|
           %IX0.4                                                      Internal   |
```
* **Boolean Equation:**  
  $$\text{OVERLOAD\_FAULT} := \text{CURRENT\_SENSOR}$$
* **How It Works:**  
  A bimetallic thermal overload relay (auxiliary contact 95-96) trips when current exceeds 15.0 A for an extended duration. This activates the internal `OVERLOAD_FAULT` flag.

---

### 🚨 Rung 4: Red Warning Fault Lamp
```text
  |---[ FAULT_LOCKOUT ]-------------------------------------------( FAULT_LAMP )---|
           Internal                                                    %QX0.2     |
```
* **Boolean Equation:**  
  $$\text{FAULT\_LAMP} := \text{FAULT\_LOCKOUT}$$
* **How It Works:**  
  Whenever the system is in a faulted safety state, the red warning lamp illuminates to notify plant personnel that maintenance or inspection is required.

---

### 🔒 Rung 5: Permanent Safety Lockout Latch (Set Coil)
```text
  |---[ OVERTEMP_FAULT ]----------------------------------------( S FAULT_LOCKOUT )|
  |        Internal                                                    Internal   |
  |                                                                               |
  |---[ OVERLOAD_FAULT ]---|                                                      |
           Internal                                                               |
```
* **Boolean Equation:**  
  $$\text{IF } (\text{OVERTEMP\_FAULT} \lor \text{OVERLOAD\_FAULT}) \implies \text{SET}(\text{FAULT\_LOCKOUT})$$
* **Why a `SET ( S )` Coil is Vital for Safety:**  
  In a normal coil `( )`, if the motor cools down from 85°C back to 70°C, the fault signal would disappear and allow the motor to restart dangerously.  
  By using a **`SET` coil**, once a fault occurs, `FAULT_LOCKOUT` **permanently latches TRUE** and will **NEVER** turn off on its own—guaranteeing fail-safe machinery isolation.

---

### 🔄 Rung 6: Safety Lockout Reset (Reset Coil)
```text
  |---[ FAULT_RESET ]-------------------------------------------( R FAULT_LOCKOUT )|
           %IX0.2                                                      Internal   |
```
* **Boolean Equation:**  
  $$\text{IF } (\text{FAULT\_RESET}) \implies \text{RESET}(\text{FAULT\_LOCKOUT})$$
* **How It Works:**  
  The safety lockout can **ONLY** be cleared when an authorized technician physically inspects the equipment and presses the `FAULT_RESET` pushbutton. Only then does `FAULT_LOCKOUT` unlatch back to FALSE, allowing Rung 0 to permit restarts.

---

## ⚡ Modbus TCP Protocol Details

Modbus TCP is the global standard for industrial fieldbus and SCADA communications (port 502/5020):

* **Coils (Function Code 01 Read, 05/15 Write):** Used for operator commands (`START`, `STOP`, `RESET`) and simulated trip switches.
* **Discrete Inputs (Function Code 02 Read-Only):** Used for reading contactor states (`MOTOR_RUN`), indicator lamps (`RUN_LAMP`, `FAULT_LAMP`), and lockout flags.
* **Holding Registers (Function Code 03 Read, 06/16 Write):** 16-bit registers used for telemetry data (Temperature in °C, Current in 0.1 A, Speed in RPM, Runtime in seconds).

---

## 📊 Live Industrial IoT Dashboard Features

The Streamlit web dashboard (`app.py`) provides:
1. **Dynamic Status Header:** Glows green (`MOTOR RUNNING`), red (`MOTOR FAULTED — SAFETY LOCKOUT ACTIVE`), or grey (`MOTOR STOPPED`).
2. **Industrial Gauges (Plotly):**
   - **Temperature Gauge:** 0–100°C with Green (0–60°C), Warning Orange (60–80°C), and Danger Red (>80°C) zones.
   - **Current Gauge:** 0–20 A with rated zone (0–12 A), warning zone (12–15 A), and trip zone (>15 A).
   - **Speed Gauge:** 0–1800 RPM with synchronous speed marker (1500 RPM).
3. **Interactive Control Console:** Remote operator buttons for Start, Stop, and Fault Reset.
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

## 🎓 The Night-Before-Interview Cheat Sheet (Top 10 Questions)

*Read this section 10 minutes before your interview at **ABB, Siemens, Schneider Electric, Rockwell, or Honeywell**!*

#### Q1: "Why did you use a seal-in latch circuit in Rung 0 instead of a toggle switch?"
> **Answer:** In industrial safety, momentary pushbuttons are required. If power drops out (blackout) and then restores, a toggle switch would automatically restart the machine, which could injure a technician or damage equipment. A seal-in latch drops out on power loss and requires an explicit, deliberate operator action to restart (No-Volt Release / Undervoltage Protection).

#### Q2: "Why is the Stop Pushbutton normally closed (NC) in industrial standards?"
> **Answer:** For fail-safe integrity (wire-break protection). If the wire connected to an NC stop button is accidentally cut or broken, the circuit immediately opens and safely stops the motor. If it were Normally Open (NO), a broken wire would mean the operator could never stop the machine in an emergency!

#### Q3: "What is the difference between a normal coil `( )` and a SET `( S )` coil in safety?"
> **Answer:** A normal coil is non-retentive: when the input condition turns off, the coil turns off. A `SET` coil is latching: once energized, it remains ON forever until a matching `RESET` coil is pulsed. In motor protection, when an overheated motor cools down, a normal coil would allow automatic restart. A `SET` coil ensures the motor stays locked out until an authorized technician inspects the system and presses Reset.

#### Q4: "What is the difference between `%IX`, `%QX`, and `%IW` in IEC 61131-3?"
> **Answer:** 
> - `%I` stands for Input, `%Q` stands for Output (from German *Quelle* / IEC standard), and `%M` stands for Internal Memory.
> - `X` denotes a single bit (`BOOL`), `B` denotes a Byte (8 bits), `W` denotes a Word (16 bits, integers/analog), and `D` denotes a Double Word (32 bits, floating point).
> - `%IX0.0` is Digital Input Bit 0; `%QX0.0` is Digital Output Bit 0; `%IW0` is Analog Input Word 0.

#### Q5: "How does Modbus TCP work, and what function codes did you use?"
> **Answer:** Modbus TCP wraps the Modbus RTU protocol inside TCP/IP packets over port 502 using a client-server architecture. In this project:
> - Function Code 01: Read Coils (operator inputs)
> - Function Code 02: Read Discrete Inputs (motor contactor & lamp states)
> - Function Code 03: Read Holding Registers (temperature, current, speed telemetry)
> - Function Code 05/15: Write Single/Multiple Coils (operator Start/Stop/Reset commands)

#### Q6: "What is a PLC scan cycle, and what was your scan rate?"
> **Answer:** A PLC scan cycle operates continuously in three steps: (1) **Read Inputs** into the Process Image Input (PII), (2) **Execute Program Logic** sequentially from top to bottom, (3) **Write Outputs** from the Process Image Output (PIQ). My gateway executes at a deterministic 100 ms scan interval (10 Hz), while industrial PLCs like Siemens S7-1500 typically run at 1–20 ms.

#### Q7: "How would you scale this architecture to monitor 50 or 100 motors in a real manufacturing plant?"
> **Answer:** In a distributed plant:
> 1. Each motor would have its own remote I/O slice or smart motor controller (e.g. Siemens SIMOCODE or ABB M-Intell) communicating over PROFINET or EtherNet/IP.
> 2. The central PLC would poll device status blocks and publish telemetry via **MQTT Sparkplug B** or **OPC-UA** to an edge gateway.
> 3. The cloud dashboard would ingest data through a time-series database (like InfluxDB or TimescaleDB) to display fleet-wide predictive health scores.

#### Q8: "How does your system implement Condition-Based Maintenance (CBM)?"
> **Answer:** By continuously streaming temperature and phase current, the system detects thermal degradation long before catastrophic insulation failure occurs. If temperature steadily creeps above 70°C at normal loads, an alert flag can schedule maintenance before the thermal relay trips.

#### Q9: "Why did you choose Ladder Diagram (LD) over Structured Text (ST) for this system?"
> **Answer:** Ladder Diagram is the standard in industrial manufacturing because maintenance engineers and electricians can visually read electrical circuit flow in real-time. For complex mathematical modeling and communications, Structured Text or Python is superior, so I used Ladder Diagram for the safety interlocking and Python for the telemetry and HMI.

#### Q10: "What fail-safe mechanism did you implement against network disconnection?"
> **Answer:** If the Modbus TCP connection drops between the web dashboard and the PLC, the PLC continues executing its internal scan cycle autonomously. The safety lockouts, overload trip logic, and stop buttons are handled locally in PLC memory, guaranteeing machine safety regardless of network status.

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

---

## 🌐 Deploy to Streamlit Community Cloud (Free)

1. Push this repository to GitHub:
   ```bash
   git remote add origin https://github.com/Rachana094/Motor_Control_System.git
   git push -u origin main
   ```
2. Navigate to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"New App"** → select `Rachana094/Motor_Control_System` → set main file to `app.py`.
4. Click **"Deploy"** — your live cloud link will be active worldwide in 60 seconds!
