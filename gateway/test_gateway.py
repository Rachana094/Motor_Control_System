"""
Quick test: Connect to PLC Gateway and test motor Start/Stop/Fault
"""
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient("127.0.0.1", port=5020)
connected = client.connect()
print(f"Connected to PLC Gateway: {connected}")

if not connected:
    print("ERROR: Cannot connect to PLC Gateway!")
    exit(1)

def read_status():
    """Read all PLC outputs and analog values."""
    di = client.read_discrete_inputs(0, 6)
    hr = client.read_holding_registers(0, 4)
    
    names = ["MOTOR_RUN", "RUN_LAMP", "FAULT_LAMP", "FAULT_LOCKOUT", "OVERTEMP", "OVERLOAD"]
    print("\n  === PLC STATUS ===")
    for i, name in enumerate(names):
        print(f"  {name:15s} = {'ON' if di.bits[i] else 'OFF'}")
    print(f"  {'TEMPERATURE':15s} = {hr.registers[0]} C")
    print(f"  {'CURRENT':15s} = {hr.registers[1]/10:.1f} A")
    print(f"  {'SPEED':15s} = {hr.registers[2]} RPM")
    print(f"  {'RUNTIME':15s} = {hr.registers[3]} sec")

# ── Test 1: Read initial state (motor should be stopped) ─────────
print("\n" + "="*50)
print("TEST 1: Initial state (Motor STOPPED)")
print("="*50)
time.sleep(0.5)
read_status()

# ── Test 2: Start the motor ──────────────────────────────────────
print("\n" + "="*50)
print("TEST 2: Pressing START button...")
print("="*50)
client.write_coil(0, True)   # START_PB = True
time.sleep(1)                 # Let a few scan cycles run
read_status()

# ── Test 3: Let motor run for 3 seconds (watch temp/speed rise) ──
print("\n" + "="*50)
print("TEST 3: Motor running for 3 seconds...")
print("="*50)
time.sleep(3)
read_status()

# ── Test 4: Simulate thermal trip ────────────────────────────────
print("\n" + "="*50)
print("TEST 4: Simulating THERMAL TRIP (overheating!)...")
print("="*50)
client.write_coil(3, True)   # TEMP_SENSOR trip = True
time.sleep(1)
read_status()

# ── Test 5: Try to restart (should fail while faulted) ───────────
print("\n" + "="*50)
print("TEST 5: Trying to restart (should FAIL - still faulted)...")
print("="*50)
client.write_coil(3, False)  # Clear thermal switch
client.write_coil(0, True)   # Try START_PB
time.sleep(1)
read_status()

# ── Test 6: Press FAULT_RESET then START ─────────────────────────
print("\n" + "="*50)
print("TEST 6: Pressing FAULT_RESET, then START...")
print("="*50)
client.write_coil(2, True)   # FAULT_RESET
time.sleep(0.5)
client.write_coil(0, True)   # START_PB
time.sleep(1)
read_status()

# ── Test 7: Press STOP ───────────────────────────────────────────
print("\n" + "="*50)
print("TEST 7: Pressing STOP button...")
print("="*50)
client.write_coil(1, True)   # STOP_PB = True
time.sleep(0.5)
client.write_coil(1, False)  # Release STOP
time.sleep(0.5)
read_status()

print("\n" + "="*50)
print("ALL TESTS COMPLETE!")
print("="*50)

client.close()

