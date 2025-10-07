import serial
import psycopg2
import time

# --- CONFIG ---
SERIAL_PORT = 'COM3'  # Arduino serial port
BAUD_RATE = 9600
DB_CONFIG = {
    'host': 'localhost',
    'database': 'plant_watering',
    'user': 'postgres',
    'password': 'admin',
    'port': 5433  # Make sure this is correct!
}
# --------------

# Connect to Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print(f"✅ Connected to Arduino on {SERIAL_PORT}")
except Exception as e:
    print("❌ Serial connection failed:", e)
    exit()

# Connect to PostgreSQL
try:
    print("Connecting to DB with config:", DB_CONFIG)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL")
except Exception as e:
    print("❌ Database connection failed:", e)
    ser.close()
    exit()

# Read loop
try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                moisture = float(line)
                cur.execute(
                    "INSERT INTO SensorData (moisturevalue) VALUES (%s)", 
                    (moisture,)
                )
                conn.commit()
                print(f"💧 Inserted moisture reading: {moisture}")
            except ValueError:
                print(f"⚠️ Invalid data from Arduino: {line}")
        time.sleep(1)  # small delay to avoid spamming
except KeyboardInterrupt:
    print("\n🛑 Stopping sensor read loop")
finally:
    cur.close()
    conn.close()
    ser.close()
    print("✅ Cleaned up connections")
