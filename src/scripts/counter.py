from collections import defaultdict
import csv

pendolari_per_fascia = defaultdict(int)

with open("res/toremove/matrice_pulita.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if "prov orig" in row[0]:
            continue

        print(row)
        
        chiave = (row[0], row[1], row[2], row[3], row[4]) # faccio una chiave per contare i pendolari da comune A a comune B, in una certa fascia oraria

        n_pendolari = int(row[-1])

        pendolari_per_fascia[chiave] += n_pendolari

for key, value in pendolari_per_fascia.items():
    print(key, value)

with open("res/toremove/matrice_comuni_sostituiti_counted.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["prov orig", "com orig", "prov dest", "com dest", "fascia oraria", "n passeggeri"])
    for key, value in pendolari_per_fascia.items():
        writer.writerow([key[0], key[1], key[2], key[3], key[4], value])
    