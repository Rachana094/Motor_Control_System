"""
=============================================================================
  PLC Motor Control Gateway — Modbus TCP Server
  Industrial IoT Smart Motor Monitoring & Control System
=============================================================================

  This script replicates the exact same ladder logic from motor_ladder.ld
  and serves all PLC variables over Modbus TCP.

  Modbus Register Map:
  ────────────────────────────────────────
  COILS (Read/Write) — Address 0-based:
    0 = START_PB       (%IX0.0)  Push to start motor
    1 = STOP_PB        (%IX0.1)  Push to stop motor
    2 = FAULT_RESET    (%IX0.2)  Push to reset fault
    3 = TEMP_SENSOR    (%IX0.3)  Thermal trip switch (simulate fault)
    4 = CURRENT_SENSOR (%IX0.4)  Overload relay trip (simulate fault)

  DISCRETE INPUTS (Read-Only) — Address 0-based:
    0 = MOTOR_RUN      (%QX0.0)  Motor contactor status
    1 = RUN_LAMP       (%QX0.1)  Green run lamp
    2 = FAULT_LAMP     (%QX0.2)  Red fault lamp
    3 = FAULT_LOCKOUT  (internal) Safety lockout active
    4 = OVERTEMP_FAULT (internal) Overtemp trip active
    5 = OVERLOAD_FAULT (internal) Overload trip active

  HOLDING REGISTERS (Read/Write):
    0 = MOTOR_TEMP     Simulated temperature in °C
    1 = MOTOR_CURRENT  Simulated current in 0.1A units
    2 = MOTOR_SPEED    Simulated speed in RPM
    3 = RUNTIME_SECS   Motor total run-time in seconds
"""

import time
import threading
import random
import socket
import logging

from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("PLC_Gateway")

# ── PLC Memory State ──────────────────────────────────────────────────
START_PB = False
STOP_PB = False
FAULT_RESET = False
TEMP_SENSOR = False
CURRENT_SENSOR = False

MOTOR_RUN = False
RUN_LAMP = False
FAULT_LAMP = False

FAULT_LOCKOUT = False
OVERTEMP_FAULT = False
OVERLOAD_FAULT = False

MOTOR_TEMP = 25.0
MOTOR_CURRENT = 0.0
MOTOR_SPEED = 0
RUNTIME_SECS = 0

scan_count = 0


def plc_scan_cycle(context):
    """
    Executes one PLC scan cycle every 100ms.
    Replicates the exact logic of motor_ladder.ld (Rungs 0 through 6).
    """
    global START_PB, STOP_PB, FAULT_RESET, TEMP_SENSOR, CURRENT_SENSOR
    global MOTOR_RUN, RUN_LAMP, FAULT_LAMP
    global FAULT_LOCKOUT, OVERTEMP_FAULT, OVERLOAD_FAULT
    global MOTOR_TEMP, MOTOR_CURRENT, MOTOR_SPEED, RUNTIME_SECS
    global scan_count

    slave = context[0x00]

    # Read inputs from Modbus coils (written by dashboard)
    coil_values = slave.getValues(1, 0, 5)
    START_PB = bool(coil_values[0])
    STOP_PB = bool(coil_values[1])
    FAULT_RESET = bool(coil_values[2])
    TEMP_SENSOR = bool(coil_values[3])
    CURRENT_SENSOR = bool(coil_values[4])

    # Rung 0: Motor Start/Stop with seal-in latch & safety interlock
    MOTOR_RUN = (START_PB or MOTOR_RUN) and (not STOP_PB) and (not FAULT_LOCKOUT)

    # Rung 1: Green Run Lamp
    RUN_LAMP = MOTOR_RUN

    # Rungs 2 & 3: Trip detection
    OVERTEMP_FAULT = TEMP_SENSOR
    OVERLOAD_FAULT = CURRENT_SENSOR

    # Rung 5: Set (S) FAULT_LOCKOUT on any trip
    if OVERTEMP_FAULT or OVERLOAD_FAULT:
        FAULT_LOCKOUT = True

    # Rung 6: Reset (R) FAULT_LOCKOUT on FAULT_RESET
    if FAULT_RESET:
        FAULT_LOCKOUT = False

    # Rung 4: Red Fault Lamp
    FAULT_LAMP = FAULT_LOCKOUT

    # Safety trip immediately kills motor
    if FAULT_LOCKOUT:
        MOTOR_RUN = False
        RUN_LAMP = False

    # Analog simulation
    if MOTOR_RUN:
        MOTOR_TEMP = min(95.0, MOTOR_TEMP + random.uniform(0.1, 0.3))
        MOTOR_CURRENT = min(200.0, max(100.0, MOTOR_CURRENT + random.uniform(-2, 3)))
        MOTOR_SPEED = min(1500, MOTOR_SPEED + random.randint(10, 50))
        RUNTIME_SECS += 1
    else:
        MOTOR_TEMP = max(25.0, MOTOR_TEMP - random.uniform(0.05, 0.2))
        MOTOR_CURRENT = max(0.0, MOTOR_CURRENT - random.uniform(1, 5))
        MOTOR_SPEED = max(0, MOTOR_SPEED - random.randint(20, 80))

    # Auto-clear momentary pushbuttons
    if START_PB:
        slave.setValues(1, 0, [0])
    if FAULT_RESET:
        slave.setValues(1, 2, [0])

    # Write outputs to discrete inputs
    slave.setValues(2, 0, [
        MOTOR_RUN,
        RUN_LAMP,
        FAULT_LAMP,
        FAULT_LOCKOUT,
        OVERTEMP_FAULT,
        OVERLOAD_FAULT,
    ])

    # Write analog telemetry to holding registers
    slave.setValues(3, 0, [
        int(MOTOR_TEMP),
        int(MOTOR_CURRENT),
        int(MOTOR_SPEED),
        int(RUNTIME_SECS),
    ])

    scan_count += 1
    if scan_count % 50 == 0:
        status = "RUNNING" if MOTOR_RUN else ("FAULTED" if FAULT_LOCKOUT else "STOPPED")
        log.info(
            f"[{status}] Temp={MOTOR_TEMP:.0f}C "
            f"Current={MOTOR_CURRENT/10:.1f}A "
            f"Speed={MOTOR_SPEED}RPM "
            f"Runtime={RUNTIME_SECS}s"
        )


def plc_scan_loop(context):
    """Continuously runs the scan cycle every 100ms."""
    log.info("PLC Scan Loop active (100ms interval).")
    while True:
        try:
            plc_scan_cycle(context)
        except Exception as e:
            log.error(f"Scan cycle error: {e}")
        time.sleep(0.1)


def create_context():
    """Create Modbus data store and server context."""
    store = ModbusSlaveContext(
        co=ModbusSequentialDataBlock(0, [0] * 16),
        di=ModbusSequentialDataBlock(0, [0] * 16),
        hr=ModbusSequentialDataBlock(0, [0] * 16),
        ir=ModbusSequentialDataBlock(0, [0] * 16),
        zero_mode=True,
    )
    return ModbusServerContext(slaves=store, single=True)


def is_port_open(host="127.0.0.1", port=5020):
    """Check if Modbus port is already open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def start_background_gateway(host="127.0.0.1", port=5020):
    """Start PLC scan engine and Modbus TCP server in background threads."""
    if is_port_open(host, port):
        log.info(f"Modbus server already running on {host}:{port}")
        return

    context = create_context()

    # Scan engine thread
    scan_th = threading.Thread(target=plc_scan_loop, args=(context,), daemon=True)
    scan_th.start()

    # Modbus server thread
    def run_server():
        StartTcpServer(context=context, address=(host, port))

    srv_th = threading.Thread(target=run_server, daemon=True)
    srv_th.start()
    time.sleep(0.5)
    log.info(f"Background Modbus server started on {host}:{port}")


def main():
    """Standalone CLI entry point."""
    log.info("Starting PLC Gateway on 127.0.0.1:5020...")
    context = create_context()
    threading.Thread(target=plc_scan_loop, args=(context,), daemon=True).start()
    StartTcpServer(context=context, address=("127.0.0.1", 5020))


if __name__ == "__main__":
    main()
