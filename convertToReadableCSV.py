#This file is unimportant for the rest of the program and just existed to try out different things




import csv
import numpy as np

#Länge von der CSV-Datei in mm
length = 1.5
#Name der Datei die eingelesen werden soll
name = 'konvex.csv'

# Öffnen der Input CSV-Datei
with open(name, 'r') as input_file:

    # Input CSV_Datei lesen
    reader = csv.reader(input_file)

    # Liste für die output_data erstellen
    output_data = []

    # Durch jede Zeile iterieren
    for row in reader:

        # Durch jeden Eintrag in der Zeile iterieren
        for i in range(len(row)):

            # Neue Zeile für jeden Eintrag erstellen und den Eintrag dann hinzufügen
            new_row = [i, row[i],0, 0]
            output_data.append(new_row)

# Öffnen von output CSV file
with open(str('output_' + name), 'w', newline='') as output_file:

    # In die CSV-Datei die Daten reinschreiben
    writer = csv.writer(output_file)
    writer.writerows(output_data)


#print(str('output_' + name))


with open(str('output_' + name), 'r') as file:
    reader = csv.reader(file)
    data = list(reader)

# Linspace vector erstellen mit gleicher Anzahl an Werten wie die CSV-Datei Zeilen hat
linspace_vector = np.linspace(0, length, len(data))

# Ersten Eintrag in jeder Reihe moodifizieren
for i, row in enumerate(data):
    row[0] = linspace_vector[i]

# Modifiziertes CSV file abspeichern
with open('modified_konvex_csv_file.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)