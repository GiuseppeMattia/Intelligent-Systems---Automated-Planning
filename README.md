# Intelligent-Systems---Automated-Planning

Project for the Automated Planning course (part of the Intelligent Systems course), Artificial Intelligence And Computer Science, Unical A.Y. 2025/26 made by Mariano Vincenzo Isabella, Antonio Manduca, Giuseppe Mattia Mezzotero, Marco Perri.

## How to run the project (on Linux)

### How to setup

* Create the folder using this command:

 ```bash
python3 -m venv venv
```

* Activate the Virtual Environment (Search the Activate bin file in the bin folder):

```bash
source venv/bin/activate
```

* At the creation of the Virtual Environment, you can use the *requirements.txt* to sync all the dependecies, use this command:

```bash
pip install -r requirements.txt 
```

* After, you should copy the provided .env file in the root level.

* Last, you should copy in the **res/sanitized** folder all the .csv files provided, and in the **res/pendolarismo** folder the *matrix_pendo2011_10112014.txt* and the *fatti_pendolarismo.asp* files.

---

### How to run code

* To make the input .asp files both for timetables and for pendolarism matrix you should run:

```bash
make init
```

---

* After that, you have several run options:

```bash
make ottimizzazione_fermate
```

Runs the first optimization about the number of stops every train makes.

---

```bash
make crea_mappa_opt_fer
```

After running the first optimization, this runs a python script to see the results on a map.

---

```bash
make ottimizzazione_number
```

Runs the second optimization about the number of trains needed to cover the trips.

---

```bash
make crea_mappa_opt_num
```

After running the second optimization, this runs a python script to see the results on a map.

---

```bash
make ottimizzazione_balance
```

Runs the third optimization about balancing train work time.

---

### Clingo stats

```bash
make ottimizzazione_fermate_stats
```

Runs the first optimization about stops with additional clingo statistics

---

```bash
make ottimizzazione_number_stats
```

Runs the second optimization about number of trains with additional clingo statistics.

---

```bash
make ottimizzazione_balance_stats
```

Runs the third optimization about balancing train work time with additional clingo statistics.

---

**NB**: The *time_tables.asp* file generates the cartesian product with all possible trips.
