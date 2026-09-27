# Fleet Telematics Analytics – Driver Risk & Fuel Efficiency Optimization

## Problem Statement
A medium sized logistics firm runs a delivery fleet in a city setting. With rising fuel prices, insurance costs due to aggressive driving, and unscheduled vehicle breakdowns reducing profitability, the firm wants insight into *what* is causing their margin reduction issues. The objective of this project is to analyze GPS data and sensor readings in order to quantify driver, vehicle, and route risk and provide specific actionable recommendations.

## Business Questions Answered
1. Who are the drivers whose behavior leads to high fuel waste and risk?
2. How much fuel is being wasted due to idling?
3. Which vehicles are reaching threshold limits and are prone to breaking down?
4. Are there certain routes/vehicles which show inefficiencies?
5. What is the risk profile of the fleet?

## Architecture

```
Data Sources → Ingestion (Python) → Storage (MySQL) → Cleaning & Transformation (SQL + Python)
→ Analytics (Driver Risk Scoring, Fuel Efficiency, Maintenance Warnings) → Visualization (Tableau)
→ Business Recommendations
```

Refer `telematics_architecture.mermaid` full diagram.

## Tech Stack
    Layer                        Tool 
1.Data generation              = Python (Faker, NumPy) 
2.Storage                      = MySQL 
3.Cleaning & transformation    = SQL, Python (pandas) 
4.Analysis                     = Python (pandas), SQL (window functions, CTEs, CASE logic) 
5.Visualization                = Tableau 
6.Version control              = GitHub 

## Dataset
Data Synthesized to Mimic 90 Days of Fleet Operations:
- **25 Vehicles**, **30 Drivers**, **Approximately 1,500 Trips**, **Approximately 1,750 Sensor Data Entries**, **70 Maintenance Logs**
- Contains known data quality problems (missing values, outlier sensor readings, duplicate records) in order to show that a true data cleanup is being done.

### Schema
- `vehicles` — vehicle_id, vehicle_number, vehicle_type, fuel_type, purchase_date
- `drivers` — driver_id, driver_name, license_number, join_date
- `trips` — trip_id, vehicle_id, driver_id, start/end time & location, distance_km, fuel_used_liters, idle_minutes
- `sensor_events` — event_id, trip_id, event_type (harsh_braking / harsh_acceleration / speeding / harsh_cornering), event_time, speed_at_event, location
- `maintenance_logs` — maintenance_id, vehicle_id, service_date, odometer_reading, service_type, cost

Data Quality Problems Identified

1.2% of trips had missing `fuel_used_liters`. Each missing value was filled using the average fuel consumption rate for that particular vehicle instead of the global average.

2.Approximately 1% of `sensor events` had an impossible speed greater than 150 km/h – considered errors by sensor/GPS and filtered out using `SQL` queries.

3.There were a few cases of duplicate trips and trips with logically inconsistent data (`end_time` is less than `start_time`, distance is zero or negative). These were detected and filtered out using `SQL` queries.

4.While cleaning `trips`, there were 30 sensor events referring to the deleted trips. Orphaned records were filtered out by cascading the deletion in Python.

5.Referential integrity was checked between `trips` and `vehicles`, `trips` and `drivers`, and `maintenance logs` and `vehicles` and there were no problems detected.

**Key lesson:** cleaning a parent table (trips) without cascading to child tables (sensor_events) silently breaks referential integrity — this was caught and fixed during the audit.

# Methodology

**1. Cleaning**
- SQL: removed duplicates, removed outlier sensor speeds, filtered logically invalid trips
- Python: imputed missing fuel values using per-vehicle average efficiency; cascaded cleanup to remove orphaned sensor events after trip-level cleaning

**2. Feature Engineering** (`feature_engineering.py`)
- Trip-level: duration, average speed, fuel efficiency (km/l), idle time %, harsh-event count
- Driver-level aggregation: total distance, total fuel used, average efficiency, average idle %, harsh events per 100 km driven
- Vehicle-level aggregation: same metrics, grouped by vehicle instead of driver

**3. Driver Risk Scoring**
Each driver's raw metrics (harsh events per 100km, idle %, fuel efficiency) were normalized to a 0–100 scale using min-max scaling, then combined using weighted scoring:

|         Factor         | Weight |                      Rationale                          |
| Harsh events per 100km | 50%    | Strongest predictor of accident risk and insurance cost |
| Idle time %            | 30%    | Direct fuel cost impact                                 |
| Fuel efficiency        | 20%    | Ongoing operating cost                                  |

Drivers are divided into **Low / Medium / High Risk** tiers based on their final score.

**4. Maintenance Alert Logic**
For each vehicle, days since last service were calculated from `maintenance_logs`, then flagged:
- **Overdue**: > 180 days since last service
- **Due Soon**: 121–180 days since last service
- **OK**: ≤ 120 days since last service

## Key Findings

**Maintenance status (25 vehicles total):**
- 🔴 **5 vehicles (20%) are overdue** for service (>180 days since last maintenance)
- 🟠 **3 vehicles (12%) are due soon** (121–180 days)
- 🟢 **17 vehicles (68%)** are up to date

**Driver risk:**
 Medium Risk: 17 drivers
 Low Risk: 13 drivers

**Top risk drivers:**
**Anya Kapoor** had the highest risk score at **62.2**
**Abdul Raj** had the second highest risk score at **61.5**
**Ekansh Dara had the third highest risk score at **61.1**

**Fleet efficiency:**
Total Distance : 35487.8	
Total Fuel : 3178.9	
Average Efficiency : 11.5

## Dashboard
Built in Tableau, connected directly to MySQL. Five views:
1. **Driver Risk Leaderboard** — Top 10 drivers ranked by risk score, color-coded by risk tier
2. **Fuel Efficiency by Vehicle** — Top 10 least efficient vehicles
3. **Idle Time % by Vehicle** — Top 10 vehicles by wasted idle time
4. **Harsh Events vs Distance** — scatter plot showing risk concentration relative to distance driven
5. **Maintenance Alerts** — vehicles ranked by days since last service,color-coded Overdue / Due Soon / OK

## How to Run This Project
1. Set up MySQL and create the database: `CREATE DATABASE vehicle_telematics;`
2. Run `data_generation.py` to produce synthetic CSV data
3. Run `data_loader.py` to create tables and load the CSVs
4. Run `manipulation.py` to calculate trip/driver/vehicle-level features and risk scores
5. Open the Tableau workbook, connect to MySQL, and explore the dashboard

## Files in This Repo
- `data_generation.py` — synthetic data generator
- `data_loader.py` — loads CSVs into MySQL with schema creation
- `manipulation.py` — feature engineering, driver/vehicle aggregation, risk scoring
- `for_cleaning.py` — final data quality audit script
- `Telematics_Architecture.png` — architecture diagram
- `README.md` — this file
- `Fleet Telematics Analytics (Driver Risk & Fuel Cost Dashboard).twbx` file

## Author
Arunprasad V — Data Analyst | Python, SQL, Tableau
LinkedIn - www.linkedin.com/in/arunprasad-v-224a2624b
GitHub - https://github.com/Arunprasad-V
Email - arunprasadv2003@gmail.com
