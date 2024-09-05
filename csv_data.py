import pandas as pd
import numpy as np
import csv

from surface import Surface


class CsvProfile(Surface):

    def __init__(self, csv_filepath: str, length: float) -> bool:
        """Init method of the Csvprofile class. For files in which the first column does not contain the y-axis values,
        a length (in mm) must be specified. For all other files, the length is ignored"""
        self.created_output_file = None
        self.path = csv_filepath
        try:
            try:
                self.load_csv(str(csv_filepath))
                self.created_output_file = False
            except:
                self.load_csv(self.convert_to_readable_csv(str(csv_filepath), length))
                self.created_output_file = True
        except:
            self.created_output_file = None

    def get_file_name(self) -> str:
        """returns the name of the csv file without the filepath attached to it"""
        # Filepath der Datei die eingelesen werden soll aufteilen, sodass nur der Dateiname übrig bleibt
        components = self.path.split("/")
        # nur filename zurückgeben
        return components[-1]

    def load_csv(self, csv_filepath: str):
        """loads the csv-file. Gets called by __init__"""

        n_skip_rows = self.find_rows_to_skip(csv_filepath) #number of rows in the csv file that can be skipped

        self.csv_doc = pd.read_csv(csv_filepath,
                                   delimiter=',',
                                   skiprows=n_skip_rows,
                                   # skips the first n rows due to the header
                                   names=['yValue', 'zValue', 'weisnicht1', 'weisnicht2'],
                                   # name the columns
                                   usecols=['yValue', 'zValue'])  # only uses these columns

    def find_rows_to_skip(self, csv_filepath: str) -> int:
        """returns how many rows of the csv file need to be skipped due to the header."""

        with open(csv_filepath, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            num_skipped_rows = 0
            for row in csv_reader:
                if len(row) >= 4:
                    break
                num_skipped_rows += 1

        if num_skipped_rows == 0:
            return 0
        else:
            return num_skipped_rows + 1



    def convert_to_readable_csv(self, csv_filepath: str, length: float) -> str:
        """converts the csv file to a format that can be read by load_csv. The first column is the y-value,
        the second column the z-value and the third and fourth column are empty or 0. convert_to_readable_csv creates
        a new file in the same folder with the name output_+name"""

        #splits the given filepath and just keeps the filename
        components = csv_filepath.split("/")
        filename = components[-1]
        filepath = ''
        for i in range(len(components) - 1):
            if filepath == '':
                filepath = components[0]
            else:
                filepath = filepath + '/' + components[i]

        # opens the csv-file
        with open(csv_filepath, 'r') as input_file:

            # reads the csv file
            reader = csv.reader(input_file)

            for i in range(self.find_rows_to_skip(csv_filepath)):
                next(reader)

            # create a list of output data
            output_data = []


            for row in reader:
                for i in range(len(row)):
                    # create new_row for every entry and add that to output_data
                    new_row = [i, row[i], 0, 0]
                    output_data.append(new_row)

        # open the output csv file
        with open(str(filepath + '/output_' + filename), 'w', newline='') as output_file:

            # write data to the output csv file
            writer = csv.writer(output_file)
            writer.writerows(output_data)

        with open(str(filepath + '/output_' + filename), 'r') as file:
            reader = csv.reader(file)
            data = list(reader)

        # create a linspace vector with the same number of values as the csv-file has rows
        linspace_vector = np.linspace(0, length, len(data))

        # modify each first entry of the row
        for i, row in enumerate(data):
            row[0] = linspace_vector[i]

        # save the modified output-csv_file in the same folder
        with open(str(filepath + '/output_' + filename), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)


        print('created', 'output_' + filename)
        return str(filepath + '/output_' + filename)

    def get_z_value(self, x: float, y: float) -> float:
        """calculates the z-value to a value x or y and returns it"""
        try:
            upperIndex = self.csv_doc[self.csv_doc['yValue'] >= y].index
            a = upperIndex[0]
        except:
            return self.csv_doc['zValue'].iloc[-1] #returns the last value of the list if the requested value is outside the list
        if a == 0:
            return self.csv_doc['zValue'].iloc[a] #returns the first value of the list if the requested value is outside the list

        z2 = self.csv_doc['zValue'].iloc[a]
        z1 = self.csv_doc['zValue'].iloc[a - 1]

        y2 = self.csv_doc['yValue'].iloc[a]
        y1 = self.csv_doc['yValue'].iloc[a - 1]

        #interpolate between the values of the list
        return (z2 - z1) / (y2 - y1) * (y - y1) + z1

    def plot_surface(self, fig, ax, width: float, number_of_surfaces: int, z_unit: int) -> None:
        """plots the surface from the csv-file. Width: maximum width of the dxf-file, res: resolution of the ramp"""

        length_of_surfaces = int(self.csv_doc.__len__() / number_of_surfaces) #calculate how many indexes 'belong' to each surface

        for i in range(0, number_of_surfaces):
            x = np.array([[-0.01, width + 0.01], [-0.01, width + 0.01]]) #add 0.02 to the width to make it look better

            if i == number_of_surfaces - 1:
                y = np.array([[self.csv_doc['yValue'].iloc[i * length_of_surfaces],
                               self.csv_doc['yValue'].iloc[i * length_of_surfaces]],
                              [self.csv_doc['yValue'].iloc[-1],
                               self.csv_doc['yValue'].iloc[-1]]])
                z = np.array([[self.csv_doc['zValue'].iloc[i * length_of_surfaces],
                               self.csv_doc['zValue'].iloc[i * length_of_surfaces]],
                              [self.csv_doc['zValue'].iloc[-1],
                               self.csv_doc['zValue'].iloc[-1]]])

            else:
                y = np.array([[self.csv_doc['yValue'].iloc[i * length_of_surfaces], self.csv_doc['yValue'].iloc[i * length_of_surfaces]],
                              [self.csv_doc['yValue'].iloc[(i+1) * length_of_surfaces], self.csv_doc['yValue'].iloc[(i+1) * length_of_surfaces]]])
                z = np.array([[self.csv_doc['zValue'].iloc[i * length_of_surfaces], self.csv_doc['zValue'].iloc[i * length_of_surfaces]],
                              [self.csv_doc['zValue'].iloc[(i+1) * length_of_surfaces], self.csv_doc['zValue'].iloc[(i+1) * length_of_surfaces]]])

            ax.plot_surface(x, y, z / z_unit, color=('#8CD5F5'), alpha=0.4)

        ax.set(xlabel='x', ylabel='y', zlabel='z')
        fig.tight_layout()

    def get_y_fine_tune(self, x1: float, y1: float, zRes: float) -> float:
        """returns the y value, at which the z difference to the last point is greater than zRes"""
        #not used right now

        z1 = self.get_z_value(x1, y1)
        z2 = z1 + zRes

        upperIndex = self.csv_doc[self.csv_doc['zValue'] >= z1].index
        upperIndex = upperIndex[0]
        i = 1
        while self.csv_doc['zValue'].iloc[upperIndex + i] < z2:
            i = i + 1
            # print(i)

        lowerIndex = upperIndex + i

        if lowerIndex > self.csv_doc.__len__():
            return self.csv_doc['yValue'].iloc[-1]
        else:
            return self.csv_doc['yValue'].iloc[lowerIndex]

    def set_rotation(self, x0: float, y0: float, phi: float) -> None:
        pass
