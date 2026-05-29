# Intelligent-Systems---Automated-Planning
Project for the Automated Planning course (part of the Intelligent Systems course), Artificial Intelligence And Computer Science, Unical

# How to run the project (on Linux)

## How to create a virtual environment

* Create the folder using this command: 
```bash
python3 -m venv venv
```
* Activate the Virtual Environment (Search the Activate bin file in the bin folder): 
```bash
source venv/bin/activate
```

At the creation of the Virtual Environment, you can use the *requirements.txt* to sync all the dependecies, use this command: 
```bash
pip install -r requirements.txt
```


# How to run clingo from terminal
```bash
python3 -m clingo src/prova.asp
```

---
---

# Possible encodings
| Encoding | Meaning |
|---|---|
| stop(Stop_id, Trip_id, Station_id, Stop_sequence). | input fact |
| stop_time(Stop_id, Arrival_time, Departure_time). | output fact |



## Scripts usage

- Inside scripts folder

```bash
python3 stopsconvertasp.py
```
simply convert from csv to asp facts of type: station(Station_id, Station_name, Zone_id).

---
```bash
python3 travel_time_calc.py
```
calculate min e max reaching time from a station to another, that are linked together, then calculate the avg and write a csv file -> 'traveltimes.csv'

---
```bash
python3 required_time_encoding.py
```
pick the two stations' ids and the avg reaching time, then write all in asp facts

---
```bash
python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/links_generator.asp | grep "connected" | tr ' ' '\n' | sed 's/$/./' > res/asp_encoding/links.asp
```
generates links.asp


---
```bash
python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/encoded_time_table.asp
```
generates encoded_time_table.asp