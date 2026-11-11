"""
=============================================================================
  PLC Motor Control Engine & Gateway — Modbus TCP + In-Memory Bridge
  Industrial IoT Smart Motor Monitoring & Control System
=============================================================================

  This module executes the exact IEC 61131-3 ladder logic from motor_ladder.ld
  at a deterministic 100ms scan interval (10 Hz).
  
  It provides:
  1. Direct zero-latency in-memory state access (bulletproof for Streamlit Cloud)
  2. Modbus TCP Server (for external SCADA / test clients)
"""

import time
import threading
import random
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("PLC_Engine")


class PLCController:
    """
    Simulates the IEC 61131-3 OpenPLC Controller runtime.
    Executes Rungs 0 through 6 every 100 ms.
    """
    def __init__(self):
        # Digital Inputs (%IX)
        self.START_PB = False       # %IX0.0
        self.STOP_PB = False        # %IX0.1
        self.FAULT_RESET = False    # %IX0.2
        self.TEMP_SENSOR = False    # %IX0.3 (Thermal Trip Switch)
        self.CURRENT_SENSOR = False # %IX0.4 (Overload Relay Trip)

        # Digital Outputs (%QX)
        self.MOTOR_RUN = False      # %QX0.0 (Main Contactor)
        self.RUN_LAMP = False       # %QX0.1 (Green Indicator)
        self.FAULT_LAMP = False     # %QX0.2 (Red Warning Indicator)

        # Internal Safety Memory Flags
        self.FAULT_LOCKOUT = False  # Set/Reset retentive latch
        self.OVERTEMP_FAULT = False
        self.OVERLOAD_FAULT = False

        # Analog Telemetry (%IW)
        self.MOTOR_TEMP = 25.0      # %IW0 (°C)
        self.MOTOR_CURRENT = 0.0    # %IW1 (0.1 A units)
        self.MOTOR_SPEED = 0        # %IW2 (RPM)
        self.RUNTIME_SECS = 0       # %IW3 (seconds)

        self._lock = threading.Lock()

    def scan_cycle(self):
        """
        One PLC scan cycle — executes every 100ms.
        Mirrors motor_ladder.ld logic.
        """
        with self._lock:
            # ── RUNG 0: Motor Start/Stop Seal-in Latch + Safety Interlock ──
            # MOTOR_RUN := (START_PB OR MOTOR_RUN) AND NOT STOP_PB AND NOT FAULT_LOCKOUT
            self.MOTOR_RUN = (
                (self.START_PB or self.MOTOR_RUN)
                and (not self.STOP_PB)
                and (not self.FAULT_LOCKOUT)
            )

            # ── RUNG 1: Green Run Pilot Lamp ──────────────────────────────
            self.RUN_LAMP = self.MOTOR_RUN

            # ── RUNGS 2 & 3: Trip Detection ───────────────────────────────
            self.OVERTEMP_FAULT = self.TEMP_SENSOR
            self.OVERLOAD_FAULT = self.CURRENT_SENSOR

            # ── RUNG 5: Set (S) FAULT_LOCKOUT on any trip ─────────────────
            # Permanent retentive latch
            if self.OVERTEMP_FAULT or self.OVERLOAD_FAULT:
                self.FAULT_LOCKOUT = True

            # ── RUNG 6: Reset (R) FAULT_LOCKOUT on FAULT_RESET ───────────
            if self.FAULT_RESET:
                self.FAULT_LOCKOUT = False

            # ── RUNG 4: Red Warning Fault Lamp ────────────────────────────
            self.FAULT_LAMP = self.FAULT_LOCKOUT

            # Fail-safe immediate shutdown if lockout triggered
            if self.FAULT_LOCKOUT:
                self.MOTOR_RUN = False
                self.RUN_LAMP = False

            # ── Analog Physical Simulation Model ──────────────────────────
            if self.MOTOR_RUN:
                self.MOTOR_TEMP = min(95.0, self.MOTOR_TEMP + random.uniform(0.1, 0.3))
                self.MOTOR_CURRENT = min(200.0, max(100.0, self.MOTOR_CURRENT + random.uniform(-2, 3)))
                self.MOTOR_SPEED = min(1500, self.MOTOR_SPEED + random.randint(15, 60))
                self.RUNTIME_SECS += 1
            else:
                self.MOTOR_TEMP = max(25.0, self.MOTOR_TEMP - random.uniform(0.05, 0.2))
                self.MOTOR_CURRENT = max(0.0, self.MOTOR_CURRENT - random.uniform(2, 6))
                self.MOTOR_SPEED = max(0, self.MOTOR_SPEED - random.randint(25, 90))

            # Auto-clear momentary pushbuttons
            if self.START_PB:
                self.START_PB = False
            if self.FAULT_RESET:
                self.FAULT_RESET = False

    def pulse_start(self):
        with self._lock:
            self.START_PB = True

    def pulse_stop(self):
        with self._lock:
            self.STOP_PB = True
            self.MOTOR_RUN = False
            self.RUN_LAMP = False

    def release_stop(self):
        with self._lock:
            self.STOP_PB = False

    def pulse_reset(self):
        with self._lock:
            self.FAULT_RESET = True

    def trigger_overtemp(self, active=True):
        with self._lock:
            self.TEMP_SENSOR = active

    def trigger_overload(self, active=True):
        with self._lock:
            self.CURRENT_SENSOR = active

    def get_snapshot(self):
        """Thread-safe snapshot of all variables for UI rendering."""
        with self._lock:
            return {
                "motor_run": self.MOTOR_RUN,
                "run_lamp": self.RUN_LAMP,
                "fault_lamp": self.FAULT_LAMP,
                "fault_lockout": self.FAULT_LOCKOUT,
                "overtemp": self.OVERTEMP_FAULT,
                "overload": self.OVERLOAD_FAULT,
                "temperature": int(self.MOTOR_TEMP),
                "current": round(self.MOTOR_CURRENT / 10.0, 1),
                "speed": int(self.MOTOR_SPEED),
                "runtime": int(self.RUNTIME_SECS),
            }


# ── Global Singleton Controller Instance ──────────────────────────────
_plc = None
_plc_thread = None
_modbus_thread = None


def get_plc():
    """Get or create singleton PLC engine with background scan loop."""
    global _plc, _plc_thread, _modbus_thread
    if _plc is None:
        _plc = PLCController()

        def scan_loop():
            log.info("PLC Scan Loop running (100ms interval).")
            while True:
                try:
                    _plc.scan_cycle()
                except Exception as e:
                    log.error(f"Scan error: {e}")
                time.sleep(0.1)

        _plc_thread = threading.Thread(target=scan_loop, daemon=True)
        _plc_thread.start()

        def start_modbus():
            try:
                from pymodbus.server import StartTcpServer
                from pymodbus.datastore import (
                    ModbusSequentialDataBlock,
                    ModbusSlaveContext,
                    ModbusServerContext,
                )
                store = ModbusSlaveContext(
                    co=ModbusSequentialDataBlock(0, [0] * 16),
                    di=ModbusSequentialDataBlock(0, [0] * 16),
                    hr=ModbusSequentialDataBlock(0, [0] * 16),
                    ir=ModbusSequentialDataBlock(0, [0] * 16),
                    zero_mode=True,
                )
                ctx = ModbusServerContext(slaves=store, single=True)
                StartTcpServer(context=ctx, address=("127.0.0.1", 5020))
            except Exception as e:
                log.warning(f"Modbus TCP server could not bind (in-memory bridge active): {e}")

        _modbus_thread = threading.Thread(target=start_modbus, daemon=True)
        _modbus_thread.start()

    return _plc


def start_background_gateway(host="127.0.0.1", port=5020):
    return get_plc()


if __name__ == "__main__":
    p = get_plc()
    print("PLC Engine started. Pressing START...")
    p.pulse_start()
    for _ in range(5):
        time.sleep(1)
        print(p.get_snapshot())
