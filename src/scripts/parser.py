import csv

rows = []

leggenda = [
"prov orig", "com orig", "prov dest", "com dest", "fascia oraria", "tempo impiegato", "n passeggeri"
]

province = {"090", "091", "092", "095", "104", "105", "106", "107"}
codice_to_provincia = {
    "090": "sassari",
    "091": "nuoro",
    "092": "cagliari",
    "095": "oristano",
    "104": "olbia-tempio",
    "105": "ogliastra",
    "106": "medio campidano",
    "107": "carbonia-iglesias"
}

with open("res/pendolarismo/matrix_pendo2011_10112014.txt", "r") as f:
    lines = f.readlines()
    
    for line in lines:
        splitted = line.split()
        if splitted[0] == "L" and splitted[2] in province and splitted[7] in province and splitted[10] == "01":
            splitted[2] = codice_to_provincia[splitted[2]]
            splitted[7] = codice_to_provincia[splitted[7]]

            # converto i codici della fascia oraria in parole
            """
            1 prima delle 7,15;
            2 dalle 7,15 alle 8,14;
            3 dalle 8,15 alle 9,14;
            4 dopo le 9,14;
            """
            
            if splitted[-4] == "1":
                splitted[-4] = "prima delle 7,15"
            elif splitted[-4] == "2":
                splitted[-4] = "dalle 7,15 alle 8,14"
            elif splitted[-4] == "3":
                splitted[-4] = "dalle 8,15 alle 9,14"
            elif splitted[-4] == "4":
                splitted[-4] = "dopo le 9,14"

            # converto i codici del tempo impiegato
            """
                1 fino a 15 minuti;
                2 da 16 a 30 minuti;
                3 da 31 a 60 minuti;
                4 oltre 60 minuti;
            """
            
            if splitted[-3] == "1":
                splitted[-3] = "fino a 15 minuti"
            elif splitted[-3] == "2":
                splitted[-3] = "da 16 a 30 minuti"
            elif splitted[-3] == "3":
                splitted[-3] = "da 31 a 60 minuti"
            elif splitted[-3] == "4":
                splitted[-3] = "oltre 60 minuti"
            
            del splitted[0]             
            del splitted[0]             # non ci serve il tipo di residenza
            del splitted[8]             # non ci serve il mezzo, abbiamo filtrato i treni
            del splitted[2:5]           # non ci serve il sesso, il motivo e se il luogo è vicino
            del splitted[4]             # non ci serve stato estero
            del splitted[-1]            # non ci serve il numero totale, sta solo nella riga summary

            splitted[-1] = str(int(float(splitted[-1])))

            

            rows.append(splitted)

for row in rows:
    print(row)

with open("res/toremove/matrice_pulita.txt", "w") as f:
    f.write(", ".join(leggenda) + "\n")
    for row in rows:
        f.write(" ".join(row) + "\n")

with open("res/toremove/matrice_pulita.csv", "w", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(leggenda)
    writer.writerows(rows)
    