# data fetching
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
host="127.0.5.1"        # server IP 
user="for_telematics"        # MySQL username
password="Password@123"       # MySQL password
database="vehicle_telematics" 
port=3300
print(repr(password))
password_encoded = quote_plus(password)
print(repr(password_encoded))
connection_string = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}"
engine = create_engine(connection_string)
with engine.connect() as connection:
    d_vehicles = pd.read_sql("SELECT * FROM vehicles", con=connection)
    d_drivers = pd.read_sql("SELECT * FROM drivers", con=connection)
    d_trips = pd.read_sql("SELECT * FROM trips", con=connection)
    d_maintenance = pd.read_sql("SELECT * FROM maintenance_logs", con=connection)
    d_sensor_events = pd.read_sql("SELECT * FROM sensor_events", con=connection)
print(d_trips.head())

# d_trips.isnull().sum()
d_trips=d_trips.dropna(subset=["fuel_used_liters"])
# print(d_sensor_events['speed_at_event'].describe())
d_sensor_events=d_sensor_events[d_sensor_events['speed_at_event']<120]
d_trips = d_trips[d_trips['end_time'] >= d_trips['start_time']]
d_trips = d_trips[d_trips['distance_km'] > 0]
d_vehicles['fuel_type'] = d_vehicles['fuel_type'].str.strip().str.title()
d_drivers['driver_name'] = d_drivers['driver_name'].str.strip()
d_sensor_events = d_sensor_events[d_sensor_events['trip_id'].isin(d_trips['trip_id'])]
orphaned_sensor_events = d_sensor_events[~d_sensor_events['trip_id'].isin(d_trips['trip_id'])]
d_vehicles["purchase_date"]=pd.to_datetime(d_vehicles["purchase_date"], errors='coerce')
d_drivers["join_date"]=pd.to_datetime(d_drivers["join_date"], errors='coerce')
print(d_vehicles['fuel_type'].unique())
print(d_vehicles['vehicle_type'].unique())
print(d_sensor_events['event_type'].unique())

d_vehicles.to_sql('vehicles_clean', engine, if_exists='replace', index=False)
d_drivers.to_sql('drivers_clean', engine, if_exists='replace', index=False)
d_trips.to_sql('trips_clean', engine, if_exists='replace', index=False)
d_sensor_events.to_sql('sensor_events_clean', engine, if_exists='replace', index=False)
d_maintenance.to_sql('maintenance_logs_clean', engine, if_exists='replace', index=False)

engine.dispose()
print("Connection closed.")