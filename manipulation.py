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
    df_vehicles = pd.read_sql("SELECT * FROM vehicles_clean", con=connection)
    df_drivers = pd.read_sql("SELECT * FROM drivers_clean", con=connection)
    df_trips = pd.read_sql("SELECT * FROM trips_clean", con=connection)
    df_sensor_events = pd.read_sql("SELECT * FROM sensor_events_clean", con=connection)

print(f"Loaded: {len(df_trips)} trips,{len(df_sensor_events)} sensor events")

"""Metrics calculated:
Fuel efficiency (km/l) per trip and per driver
Idle time % per vehicle
Harsh-event frequency per driver per 100 km
Average speed per trip
Driver-level summary table"""
# TRIP-LEVEL FEATURES
print(df_trips.head(3))
df_trips['start_time'] = pd.to_datetime(df_trips['start_time'])
df_trips['end_time'] = pd.to_datetime(df_trips['end_time'])
df_trips['duration_hours'] = (df_trips['end_time'] - df_trips['start_time']).dt.total_seconds() / 3600
df_trips['avg_speed_kmph'] = df_trips['distance_km'] / df_trips['duration_hours']
df_trips['fuel_efficiency_kmpl'] = df_trips.apply(
    lambda row: row['distance_km'] / row['fuel_used_liters'] if row['fuel_used_liters'] > 0 else None,
    axis=1
)
df_trips['idle_pct'] = (df_trips['idle_minutes'] / (df_trips['duration_hours'] * 60)) * 100

print("\nTrip-level features calculated:")
print(df_trips[['trip_id', 'avg_speed_kmph', 'fuel_efficiency_kmpl', 'idle_pct']].head())
print(df_trips.columns.to_list())

# HARSH EVENT COUNT PER TRIP
harsh_events_per_trip = df_sensor_events.groupby('trip_id').size().reset_index(name='harsh_event_count')
print(df_trips.columns.to_list())
df_trips = df_trips.merge(harsh_events_per_trip, on='trip_id', how='left')
df_trips['harsh_event_count'] = df_trips['harsh_event_count'].fillna(0)
# Harsh events normalized per 100 km driven
df_trips['harsh_events_per_100km'] = (df_trips['harsh_event_count'] / df_trips['distance_km']) * 100
print(df_trips.columns.to_list())

# DRIVER-LEVEL AGGREGATION
driver_summary = df_trips.groupby('driver_id').agg(
    total_trips=('trip_id', 'count'),
    total_distance_km=('distance_km', 'sum'),
    total_fuel_liters=('fuel_used_liters', 'sum'),
    avg_fuel_efficiency_kmpl=('fuel_efficiency_kmpl', 'mean'),
    avg_idle_pct=('idle_pct', 'mean'),
    total_harsh_events=('harsh_event_count', 'sum'),
    avg_speed_kmph=('avg_speed_kmph', 'mean')
).reset_index()
# Harsh events per 100km at driver level
driver_summary['harsh_events_per_100km'] = (
    driver_summary['total_harsh_events'] / driver_summary['total_distance_km']
) * 100
driver_summary = driver_summary.merge(df_drivers[['driver_id', 'driver_name']], on='driver_id', how='left')

# idle %, efficiency by vehicle
vehicle_summary = df_trips.groupby('vehicle_id').agg(
    total_trips=('trip_id', 'count'),
    total_distance_km=('distance_km', 'sum'),
    avg_fuel_efficiency_kmpl=('fuel_efficiency_kmpl', 'mean'),
    avg_idle_pct=('idle_pct', 'mean'),
    total_harsh_events=('harsh_event_count', 'sum')
).reset_index()

vehicle_summary = vehicle_summary.merge(
    df_vehicles[['vehicle_id', 'vehicle_number', 'vehicle_type']], on='vehicle_id', how='left'
)

df_trips.to_sql('trips_features', engine, if_exists='replace', index=False)
driver_summary.to_sql('driver_summary', engine, if_exists='replace', index=False)
vehicle_summary.to_sql('vehicle_summary', engine, if_exists='replace', index=False)

print("\nFeature tables written to MySQL: trips_features, driver_summary, vehicle_summary")

def normalize(series, higher_is_worse=True):
    min_val, max_val = series.min(), series.max()
    if higher_is_worse:
        return (series - min_val) / (max_val - min_val) * 100
    else:
        return (max_val - series) / (max_val - min_val) * 100  # invert for efficiency (lower = worse)

driver_summary['idle_score'] = normalize(driver_summary['avg_idle_pct'], higher_is_worse=True)
driver_summary['harsh_score'] = normalize(driver_summary['harsh_events_per_100km'], higher_is_worse=True)
driver_summary['efficiency_score'] = normalize(driver_summary['avg_fuel_efficiency_kmpl'], higher_is_worse=False)

WEIGHT_HARSH = 0.5      # safety/accident risk
WEIGHT_IDLE = 0.3       # fuel waste
WEIGHT_EFFICIENCY = 0.2 # cost efficiency

driver_summary['risk_score'] = (
    driver_summary['harsh_score'] * WEIGHT_HARSH +
    driver_summary['idle_score'] * WEIGHT_IDLE +
    driver_summary['efficiency_score'] * WEIGHT_EFFICIENCY
)

driver_summary = driver_summary.sort_values('risk_score', ascending=False)
def risk_tier(score):
    if score >= 70:
        return 'High Risk'
    elif score >= 40:
        return 'Medium Risk'
    else:
        return 'Low Risk'

driver_summary['risk_tier'] = driver_summary['risk_score'].apply(risk_tier)
driver_summary.to_sql('driver_risk_scores', engine, if_exists='replace', index=False)


engine.dispose()
print("Connection closed.")