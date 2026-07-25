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


```bash
python3 src/scripts/stopsconvertasp.py
```
simply convert from csv to asp facts of type: station(Station_id, Station_name, Zone_id).

---
```bash
python3 src/scripts/travel_time_calc.py
```
calculate min e max reaching time from a station to another, that are linked together, then calculate the avg and write a csv file -> 'traveltimes.csv'

---
```bash
python3 src/scripts/required_time_encoding.py
```
pick the two stations' ids and the avg reaching time, then write all in asp facts

---
```bash
python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/links_generator.asp | grep "connected" | tr ' ' '\n' | sed 's/$/./' > res/asp_encoding/links.asp
```
generates links.asp
**WARNING** The command works only for Linux environments, if you are in Windows try this
```bash
python -m clingo res/asp_encoding/stops.asp src/asp_scripts/links_generator.asp | Select-String "connected" | ForEach-Object { $_.Line -split ' ' } | ForEach-Object { "$_." } | Set-Content res/asp_encoding/links.asp
```

---
```bash
python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/encoded_time_table.asp
```
generates encoded_time_table.asp 
**WARNING** Again, if you are in Windows the command is syntactically different: create the "output" folder inside res and then try to run the following:
```bash
python -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | Select-String "station" | ForEach-Object { $_.Line -split ' ' } | ForEach-Object { "$_." } | Set-Content res/output/encoded_time_table.asp
```

---
```bash
python3 src/scripts/map.py
```
reconstructs train routes from the ASP facts (`first_station` and `next_station` in `encoded_time_table.asp`) and station coordinates from `stops.csv`, and generates an interactive geographical Leaflet map (saved to `train_map.html` or the location specified by `PATH_TO_MAP_OUTPUT` in `.env`) complete with custom color themes, light/dark modes, filters, tooltips, and statistics.

**NB** time_tables.asp stays as is the file that generates the cartesian product. Consequently, also links_generator.asp stays.
Also stopsconvertasp.py stays due to this