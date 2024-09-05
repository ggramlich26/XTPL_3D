import math

import numpy as np
import ezdxf
import csv_data
import copy

import sdf_data
import surface
import time


class Dxf2D:

    def __init__(self, dxfName: str):
        self.dxfName = dxfName
        self.points = []  # the points read from the .dxf file
        self.offsetX = 0  # the x offset applied
        self.offsetY = 0  # the y offset applied
        self.surfacePhi = 0  # the rotation which is applied to the surface
        self.projectionMethod = 'longest segments'
        self.z_resolution = 0
        self.z_unit = 0
        self.read_file(dxfName)
        # Instanz erstellt
        # Dprint(self.get_dxf_name(), 'loaded')
        self.points_projected = []  # store the projected points for reuse until a different offset is applied or the the surface changes
        self.projection_valid = False  # has to be set to False whenever the offset, rotation, projection method or surface changes

    def get_dxf_name(self) -> str:
        """Returns just the name of the dxf file, without the path"""
        # split  the filepath
        components = self.dxfName.split("/")
        # return just the filename
        return components[-1]

    def read_file(self, dxfName: str) -> None:
        """Reads the dxf file and writes the start- and end-coordinates of the polylines into the points-list of the object."""

        doc = ezdxf.readfile(dxfName)
        msp = doc.modelspace()

        # iterates through each layer and creates a list of the start- middle- and end-coordinates of the polylines.
        polylines = msp.query("LWPOLYLINE")

        for line in polylines:
            if doc.layers.get(line.dxf.layer).is_off():
                continue
            l = []

            for i in range(0, len(line)):
                # append each points x- and y-coordinates to l.
                l.append([copy.copy(line[i][0]), copy.copy(line[i][1])])

            # if the line is closed, the start-coordinates will be appended to the end of the list
            if line.is_closed:
                l.append([copy.copy(line[0][0]), copy.copy(line[0][1])])

            self.points.append(l)
        # print(self.points)

        # detection of normal lines instead of polylines can be added here
        """# geht die layer durch und erstellt eine Liste mit allen Anfangs und End-Koordinaten der normalen Lines.
        lines = msp.query('LINE')
        k = []
        for line in lines:
            if doc.layers.get(line.dxf.layer).is_off():
                continue
            x1 = line.dxf.start[0]
            y1 = line.dxf.start[1]
            # z1 = line.dxf.start[2]
            x2 = line.dxf.end[0]
            y2 = line.dxf.end[1]
            # z2 = line.dxf.end[2]

            self.points.append([[x1, y1], [x2, y2]])  # schreibt die Werte direkt in das Attribut des Objektes"""

        def correct_y_direction(points: list) -> list:
            """checks the y-Axis movement and breaks the polylines if the coordinates change the direction. Additionally, it flips the descending lists, so that all y-movements are only in the positive direction"""
            # check if the polylines change their y-direction an breaks them apart if they do
            new_list = []
            current_sublist = []
            current_direction = None
            for i, polyline in enumerate(points):
                for j, coordinates in enumerate(polyline):
                    if j == 0:
                        current_sublist.append(copy.copy(coordinates))
                        continue
                    if coordinates[1] > polyline[j - 1][1]:
                        if current_direction == 'DESCENDING':
                            new_list.append(current_sublist)
                            current_sublist = []
                            current_sublist.append(copy.copy(polyline[j - 1]))
                        current_direction = 'ASCENDING'
                    elif coordinates[1] < polyline[j - 1][1]:
                        if current_direction == 'ASCENDING':
                            new_list.append(current_sublist)
                            current_sublist = []
                            current_sublist.append(copy.copy(polyline[j - 1]))
                        current_direction = 'DESCENDING'
                    current_sublist.append(copy.copy(coordinates))
                new_list.append(current_sublist)
                current_direction = None
                current_sublist = []

            # checks if the lists are in ascending or descending order and flips them if necessary
            for k, polyline in enumerate(new_list):
                if polyline[0][1] < polyline[-1][1]:
                    continue
                else:
                    new_list[k] = polyline[::-1]

            return new_list

        self.points = correct_y_direction(self.points)

    # add_values_in_between and add_values_in_between_v2 are not used right now
    def add_values_in_between_3(self, surface: csv_data.CsvProfile, z_resolution: float, xyRes: float) -> list:
        """Fügt zwischen den Start- und Endpunkten der Polylines punkte hinzu, sodass die Annäherung an die
        Oberfläche genauer wird. res gibt an, wie genau unterteilt wird. Achtung, es wird in x- und y-Richtung
        unterteilt, nicht in z-Richtung. Alle Werte werden überprüft und nur die Werte mit entsprechend großem
        Z-Abstand zum vorherigen Wert werden übernommen. zRes: Auflösung in z-Richtung, xyRes: Auflösung in xy-Richtung"""

        # nicht perfekt gelöst, jetzt werden immer die lines unterbrochen, auch wenn sie keinen Höhenunterschied aufweisen würden. Aber nur die Werte mit groß genugem Z-Abstand werden nachher auch genutzt

        points_extended = []
        # print(self.points)
        # print('z_resolution=', z_resolution)
        for i in range(self.points.__len__()):
            mid_list = []
            for j in range(self.points[i].__len__() - 1):
                l = []
                x1 = self.points[i][j][0]
                x2 = self.points[i][j + 1][0]
                y1 = self.points[i][j][1]
                y2 = self.points[i][j + 1][1]

                yAbstand = y1 - y2

                # print(yAbstand, 'bin jetzt hier')

                yVec = np.linspace(y1, y2, int(abs(yAbstand / xyRes)))
                xVec = np.linspace(x1, x2, int(abs(yAbstand / xyRes)))
                zVec = []

                # Failsave, wenn die xy-Auflösung zu grob ist, Programm wird beendet mit Fehlermeldung

                if len(yVec) == 0:
                    # if self.add_values_in_between not in globals():
                    raise ('xy-Auflösung zu grob')

                # fragt ab wie groß der z-Abstand ist und wenn er den schwellenwert von z_resolution überschreitet, wird der Wert hinzugefügt
                for k in range(len(yVec)):
                    # print('länge yVec:', len(yVec))
                    # if (abs(surface.get_z_value(0, yVec[k]) - surface.get_z_value(0, l[-1][-1]))) == 0:

                    if k == 0 or k == len(yVec) - 1:
                        l.append([xVec[k], yVec[k]])
                        # counter += 1
                        # print('if', counter)

                    elif (abs(surface.get_z_value(0, yVec[k]) - surface.get_z_value(0, l[-1][-1]))) > z_resolution:
                        l.append([xVec[k], yVec[k]])
                        # print('bin in elif')
                    else:
                        pass
                # Todo: add_values_inbetween ändern, sodass die Liste um eine Dimension flacher wird.
                # alternative Lösung, aber ohne entfernen der Werte die keinen groß genugen Abstand aufweisen:
                """for k in range(yVec.__len__()):
                    l.append([xVec[k], yVec[k]])"""
                mid_list.append(l)
            # print('added', counter, 'values in between')
            # print(l)
            # self.points = points_extended
            points_extended.append(mid_list)
        return points_extended

    def add_values_in_between(self, surface: csv_data.CsvProfile, z_resolution: float, xyRes: float) -> list:
        """Adds values inbetween the start- and end-coordinates of the polyline. This enables the line to be closer to
        the surface. res determines the accuracy of the fit. zRes: accuracy of the fit in z-direction. xyRes: accuracy
        of the fit in xy-direction."""

        points_extended = []
        for polyline_list in self.points:
            mid_list = []
            for i in range(len(polyline_list) - 1):
                mid_list.append(polyline_list[i])
                try:  # if polyline_list is only 2-dimensional
                    x1, y1 = polyline_list[i]
                    x2, y2 = polyline_list[i + 1]
                except:  # if polyline_list has been already created once and therefor is 3-dimensional
                    x1, y1, z1 = polyline_list[i]
                    x2, y2, z2 = polyline_list[i + 1]

                yAbstand = y1 - y2

                yVec = np.linspace(y1, y2, int(abs(yAbstand / xyRes)))  # create yVec

                xVec = np.linspace(x1, x2, int(abs(yAbstand / xyRes)))  # create xVec

                if len(yVec) == 0:
                    continue
                # if the z-distance of the last added point to the current point is greater or equal to z_resolution AND the current point is not the fir OR the last point of the vector, it gets added to the list
                for k in range(len(yVec) - 1):
                    if (abs(surface.get_z_value(0, yVec[k]) - surface.get_z_value(0, mid_list[-1][
                        1]))) >= z_resolution and (xVec[k] != xVec[-1] or yVec[k] != yVec[-1]):
                        mid_list.append([xVec[k], yVec[k]])

            mid_list.append(polyline_list[-1])
            points_extended.append(mid_list)
        return points_extended

    def add_values_in_between_v2(self, surface: csv_data.CsvProfile) -> list:
        """erhält die nächste y-Koordinate aus csv_data.getYFineTune() die einen um zRes verschobenen
        z-Achsenabschnitt hat und erstellt daraus eine Liste mit allen Punkten, die die Polylines approximieren. Die
        Start- und Endpunkte der Polylines sind Teil des Objekts, dessen die Funktion aufgerufen wird."""
        # Aufgabe für Zukunfts-Jonathan

        csv_data.CsvProfile.getYFineTune()

    def project(self, surface: csv_data.CsvProfile, z_resolution: float) -> list:
        """Projects the dxf polylines on to the given surface. Returns a list with the according z-coordinates of the
        given xy-coordinates"""

        points3D = self.add_values_in_between(surface, z_resolution, 0.001)

        # fragt ab wie lange die Liste ist, damit sie nicht immer um einen neuen Z-Wert erweitert wird, sondern der alte ersetzt wird, so wird die Liste bei mehrfacher ausführung der project-Funktion nicht länger
        '''if self.project in globals():
            print('zweiter Durchlauf')'''
        for i in range(points3D.__len__()):
            for j in range(0, points3D[i].__len__()):

                # erstellt jedes Mal eine neue Liste, darum brauchen wir keine Abfrage, ob schon ein z-Wert hinzugefügt worden ist oder nicht.
                if len(points3D[i][j]) == 2:
                    points3D[i][j].insert(2, surface.get_z_value(0, points3D[i][j][1]))
                else:
                    points3D[i][j][2] = surface.get_z_value(0, points3D[i][j][1])

        return points3D

    def project_z_steps(self, surf: surface.Surface, z_resolution: float) -> list:
        """Projects the dxf polylines on to the given surface. Returns a list with the according z-coordinates of the given xy-coordinates"""
        xy_res = 0.5 # in um
        points3D = []

        for pline in self.points:
            templine = []
            for i in range(len(pline) - 1):
                x1 = pline[i][0]*1000
                y1 = pline[i][1]*1000
                x2 = pline[i + 1][0]*1000
                y2 = pline[i + 1][1]*1000
                dx = x2 - x1
                dy = y2 - y1
                dist = math.sqrt(dx ** 2 + dy ** 2)
                last_z = np.round(surf.get_z_value(x1/1000, y1/1000), decimals=2)
                templine.append([x1/1000, y1/1000, last_z])
                npoints = round(dist / xy_res)
                for j in range(1, npoints):
                    x = x1 + dx * j / npoints
                    y = y1 + dy * j / npoints
                    z = np.round(surf.get_z_value(x/1000, y/1000), decimals=2)
                    if abs(z - last_z) >= z_resolution:
                        templine.append([x/1000, y/1000, z])
                        last_z = z
            x = pline[-1][0]
            y = pline[-1][1]
            z = surf.get_z_value(x, y)
            templine.append([x, y, z])
            points3D.append(templine)

        return points3D

    def project_const_seg_len(self, surf: surface.Surface, seg_len: float) -> list:
        """Projects the dxf polylines on to the given surface using segments of a constant and specified length. Returns a list with the according z-coordinates of the given xy-coordinates"""
        xy_res = 0.1 # in um
        points3D = []

        for pline in self.points:
            templine = []
            for i in range(len(pline) - 1):
                x1 = pline[i][0]*1000
                y1 = pline[i][1]*1000
                x2 = pline[i + 1][0]*1000
                y2 = pline[i + 1][1]*1000
                dx = x2 - x1
                dy = y2 - y1
                dist = math.sqrt(dx ** 2 + dy ** 2)
                last_x = x1
                last_y = y1
                last_z = np.round(surf.get_z_value(x1/1000, y1/1000), decimals=2)
                templine.append([x1/1000, y1/1000, last_z])
                npoints = round(dist / xy_res)
                for j in range(1, npoints):
                    x = x1 + dx * j / npoints
                    y = y1 + dy * j / npoints
                    z = np.round(surf.get_z_value(x/1000, y/1000), decimals=2)
                    tmp_dist = math.sqrt((x - last_x)**2 + (y - last_y)**2 + (z - last_z)**2)
                    if tmp_dist >= seg_len:
                        templine.append([x/1000, y/1000, z])
                        last_x = x
                        last_y = y
                        last_z = z
            # append last point of polyline if not already there
            if templine[-1][0] != pline[-1][0] or templine[-1][1] != pline[-1][1]:
                x = pline[-1][0]
                y = pline[-1][1]
                z = surf.get_z_value(x, y)
                templine.append([x, y, z])
            points3D.append(templine)

        return points3D

    def project_v3(self, surf: surface.Surface, z_resolution: float) -> list:
        """Projects the dxf polylines on to the given surface. This is done by using the longest possible linear
        approximation. Once the maximum distance between the linear approximation and the real profile exceeds
        z_resolution, a new point will be inserted. All corner points of polylines will be kept.
        Returns a list with 3D polylines."""
        xy_res = 0.001
        points3D = []

        for pline in self.points:
            templine = []
            for i in range(len(pline) - 1):
                x1 = pline[i][0]
                y1 = pline[i][1]
                x2 = pline[i + 1][0]
                y2 = pline[i + 1][1]
                dx = x2 - x1
                dy = y2 - y1
                dist = math.sqrt(dx ** 2 + dy ** 2)
                z_hist = [surf.get_z_value(x1, y1)]
                templine.append([x1, y1, z_hist[0]])
                npoints = round(dist / xy_res)
                for j in range(1, npoints):
                    x = x1 + dx * j / npoints
                    y = y1 + dy * j / npoints
                    z_hist.append(surf.get_z_value(x, y))
                    if len(z_hist) > 2:
                        mz = (z_hist[-1] - z_hist[0]) / len(z_hist)
                        for k in range(1, len(z_hist)):
                            if abs(z_hist[0] + k * mz - z_hist[k]) >= z_resolution:
                                templine.append([x1 + dx * (j - 1) / npoints, y1 + dy * (j - 1) / npoints, z_hist[-2]])
                                z_hist = z_hist[-2:]
                                break
            x = pline[-1][0]
            y = pline[-1][1]
            z = surf.get_z_value(x, y)
            templine.append([x, y, z])
            points3D.append(templine)

        return points3D

    def set_shift(self, offsetX: float, offsetY: float) -> None:
        """Updates the shift of the dxf file and possibly invalidates the projection."""

        dx = offsetX - self.offsetX
        dy = offsetY - self.offsetY
        self.offsetX = offsetX
        self.offsetY = offsetY
        if 0 == dx and 0 == dy:
            return

        # update shift in points
        for line in self.points:
            for coordinates in line:
                coordinates[0] += dx
                coordinates[1] += dy

        # if the shift has been changed, the projection is invalid
        self.invalidateProjection()

    def set_rotation(self, phi: float):
        if phi != self.surfacePhi:
            self.invalidateProjection()
            self.surfacePhi = phi

    def set_projection_method(self, method: str):
        if self.projectionMethod == method:
            return
        elif not (method in ['const. seg. len.', 'z', 'longest segments']):
            print('invalid projection method')
            return
        self.projectionMethod = method
        self.invalidateProjection()

    def plot_to_surface(self, fig, ax, surf: surface.Surface, z_resolution: float, z_unit: int) -> int:
        """Plots the dxf file onto the surface. Furthermore, it updates the points_export list to the current
        coordinates. Returns the number of points after the projection."""
        col = color = (0.63529, 0.133333, 0.13725)
        # height data of SdfSurface is always given in um. -> set z_unit to 1
        if isinstance(surf, sdf_data.SdfSurface):
            z_unit = 1
            col = color = (0, 0, 0)
        if self.z_resolution != z_resolution or self.z_unit != z_unit:
            self.invalidateProjection()
            self.z_resolution = z_resolution
            self.z_unit = z_unit
        if not self.projection_valid:
            if self.projectionMethod == 'const. seg. len.':
                self.points_projected = self.project_const_seg_len(surf, z_resolution)
            elif self.projectionMethod == 'z':
                self.points_projected = self.project_z_steps(surf, z_resolution * z_unit)
            else:
                # longest segments
                self.points_projected = self.project_v3(surf, z_resolution * z_unit)
            self.projection_valid = True

        for pline in self.points_projected:
            x = [x for x, y, z in pline]
            y = [y for x, y, z in pline]
            z = [z for x, y, z in pline]
            ax.plot(x, y, z, color=col)

        npoints = 0
        for pline in self.points_projected:
            npoints += len(pline)
        return npoints

    def width(self) -> float:
        """findet maximale Breite der DXF-Datei (Annahme, dass die ersten Werte in der Liste die ersten Polylines sind)"""
        min_x = []
        max_x = []
        for polyline in self.points:
            x_values = [point[0] for point in polyline]
            min_x.append(min(x_values))
            max_x.append(max(x_values))

        width = max(max_x) - min(min_x)
        return width

    def get_points(self, surf: surface.Surface, z_unit: int) -> list:
        """returns the points list after the projection with the shift being subtracted from the x and y coordinates"""
        if not self.projection_valid:
            raise "Projection invalid. Please run render before exporting."
        # heigt data of SdfSurface is always given in um. -> set z_unit to 1
        if isinstance(surf, sdf_data.SdfSurface):
            z_unit = 1
        offsetZ = surf.get_z_value(self.offsetX, self.offsetY)

        points_export = copy.deepcopy(self.points_projected)
        for pline in points_export:
            for point in pline:
                point[0] -= self.offsetX
                point[1] -= self.offsetY
                point[2] = - (point[2] - offsetZ) / (
                        z_unit * 1000)  # divide by (z_unit*1000) to set the z-axis to mm instead of µm. '-' since the coordinate system of the printer has a rotated z-axis

        return points_export

    def invalidateProjection(self):
        self.projection_valid = False
