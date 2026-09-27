"""
Telematics Synthetic Data Generator
------------------------------------
Generates realistic data for: vehicles, drivers, trips, sensor_events, maintenance_logs
Outputs CSV files ready to load into PostgreSQL/SQLite."""

import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

# CONFIG 
NUM_VEHICLES = 25
NUM_DRIVERS = 30
NUM_TRIPS = 1500
SIMULATION_DAYS = 90
CITY_CENTER_LAT = 13.0827   # Chennai
CITY_CENTER_LONG = 80.2707

VEHICLE_TYPES = ["Mini Truck", "Van", "Pickup", "Tempo"]
FUEL_TYPES = ["Diesel", "Petrol", "CNG"]
EVENT_TYPES = ["harsh_braking", "harsh_acceleration", "speeding", "harsh_cornering"]
SERVICE_TYPES = ["Oil Change", "Brake Inspection", "Tyre Replacement", "General Service", "Engine Check"]


def random_datetime_within(days_back):
    start = datetime.now() - timedelta(days=days_back)
    random_seconds = random.randint(0, days_back * 24 * 3600)
    return start + timedelta(seconds=random_seconds)


def random_point_near(lat, long, radius_km=15):
    # rough approximation: 1 degree ~ 111km
    delta_lat = random.uniform(-radius_km, radius_km) / 111
    delta_long = random.uniform(-radius_km, radius_km) / 111
    return round(lat + delta_lat, 6), round(long + delta_long, 6)

# 1. VEHICLES
vehicles = []
for i in range(1, NUM_VEHICLES + 1):
    vehicles.append({
        "vehicle_id": i,
        "vehicle_number": f"TN{random.randint(10,99)}AB{random.randint(1000,9999)}",
        "vehicle_type": random.choice(VEHICLE_TYPES),
        "fuel_type": random.choice(FUEL_TYPES),
        "purchase_date": fake.date_between(start_date="-4y", end_date="-6m")
    })
df_vehicles = pd.DataFrame(vehicles)

# 2. DRIVERS
drivers = []
for i in range(1, NUM_DRIVERS + 1):
    drivers.append({
        "driver_id": i,
        "driver_name": fake.name(),
        "license_number": f"TN{random.randint(10,99)}{random.randint(100000,999999)}",
        "join_date": fake.date_between(start_date="-3y", end_date="-1m")
    })
df_drivers = pd.DataFrame(drivers)

# 3. TRIPS
trips = []
for trip_id in range(1, NUM_TRIPS + 1):
    vehicle_id = random.randint(1, NUM_VEHICLES)
    driver_id = random.randint(1, NUM_DRIVERS)
    start_time = random_datetime_within(SIMULATION_DAYS)

    distance_km = round(np.random.gamma(shape=3, scale=8), 2)  
    avg_speed_kmph = random.uniform(20, 45)
    duration_hours = distance_km / avg_speed_kmph
    end_time = start_time + timedelta(hours=duration_hours)

    start_lat, start_long = random_point_near(CITY_CENTER_LAT, CITY_CENTER_LONG)
    end_lat, end_long = random_point_near(CITY_CENTER_LAT, CITY_CENTER_LONG)

    base_efficiency = random.uniform(8, 15)  # km/l
    fuel_used = round(distance_km / base_efficiency, 2)

    idle_minutes = int(np.random.exponential(scale=8)) 

    trips.append({
        "trip_id": trip_id,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "start_time": start_time,
        "end_time": end_time,
        "start_lat": start_lat,
        "start_long": start_long,
        "end_lat": end_lat,
        "end_long": end_long,
        "distance_km": distance_km,
        "fuel_used_liters": fuel_used,
        "idle_minutes": idle_minutes
    })
df_trips = pd.DataFrame(trips)

# 4. SENSOR EVENTS (harsh braking, speeding, etc.)
sensor_events = []
event_id = 1
for _, trip in df_trips.iterrows():
    # number of harsh events per trip - some drivers trigger more (simulated risk variance)
    num_events = np.random.poisson(lam=1.2)
    for _ in range(num_events):
        event_time = trip["start_time"] + timedelta(
            seconds=random.randint(0, int((trip["end_time"] - trip["start_time"]).total_seconds()))
        )
        lat, long = random_point_near(trip["start_lat"], trip["start_long"], radius_km=5)
        sensor_events.append({
            "event_id": event_id,
            "trip_id": trip["trip_id"],
            "event_type": random.choice(EVENT_TYPES),
            "event_time": event_time,
            "speed_at_event": round(random.uniform(40, 90), 1),
            "latitude": lat,
            "longitude": long
        })
        event_id += 1
df_sensor_events = pd.DataFrame(sensor_events)

# 5. MAINTENANCE LOGS
maintenance_logs = []
maintenance_id = 1
for vehicle_id in range(1, NUM_VEHICLES + 1):
    num_services = random.randint(1, 4)
    odometer = random.randint(5000, 20000)
    for _ in range(num_services):
        odometer += random.randint(2000, 6000)
        maintenance_logs.append({
            "maintenance_id": maintenance_id,
            "vehicle_id": vehicle_id,
            "service_date": fake.date_between(start_date="-1y", end_date="today"),
            "odometer_reading": odometer,
            "service_type": random.choice(SERVICE_TYPES),
            "cost": round(random.uniform(800, 8000), 2)
        })
        maintenance_id += 1
df_maintenance = pd.DataFrame(maintenance_logs)

# Randomly null out a few fuel_used values
null_indices = df_trips.sample(frac=0.02).index
df_trips.loc[null_indices, "fuel_used_liters"] = np.nan

# Inject a few unrealistic outlier speeds into sensor_events
outlier_indices = df_sensor_events.sample(frac=0.01).index
df_sensor_events.loc[outlier_indices, "speed_at_event"] = random.uniform(150, 220)

# ---------------------------
# EXPORT TO CSV
# ---------------------------
df_vehicles.to_csv(r"C:\Telematics\source_file\vehicles.csv", index=False)
df_drivers.to_csv(r"C:\Telematics\source_file\drivers.csv", index=False)
df_trips.to_csv(r"C:\Telematics\source_file\trips.csv", index=False)
df_sensor_events.to_csv(r"C:\Telematics\source_file\sensor_events.csv", index=False)
df_maintenance.to_csv(r"C:\Telematics\source_file\maintenance_logs.csv", index=False)

print("Data generation complete:")
print(f"  vehicles.csv        -> {len(df_vehicles)} rows")
print(f"  drivers.csv         -> {len(df_drivers)} rows")
print(f"  trips.csv           -> {len(df_trips)} rows")
print(f"  sensor_events.csv   -> {len(df_sensor_events)} rows")
print(f"  maintenance_logs.csv-> {len(df_maintenance)} rows")