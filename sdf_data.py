import numpy as np
import math
from scipy.interpolate import RegularGridInterpolator
from matplotlib import cm

from surface import Surface


class SdfSurface(Surface):

    def __init__(self, filepath: str) -> bool:
        """Init method of the SdfSurface class."""
        self.path = filepath
        self.numPoints = None
        self.numProfiles = None
        self.xScale = None
        self.yScale = None
        self.zScale = None
        self.data = {}
        self.interp = None
        self.colorbarPlotted = False
        self.rotX = 0
        self.rotY = 0
        self.rotPhi = 0

        self.load_sdf(filepath)
        self.interpolate_holes()

        #create axes for plot and interpolation
        x = np.linspace(start=0, stop=self.data['numPoints'] * self.data['xScale']*1000, num=self.data['numPoints'],
                        endpoint=False)
        y = np.linspace(start=0, stop=self.data['numProfiles'] * self.data['yScale']*1000, num=self.data['numProfiles'],
                        endpoint=False)
        self.data['x'], self.data['y'] = np.meshgrid(x, y)
        self.interp = RegularGridInterpolator((y,x), self.data['z'], bounds_error=False, fill_value=None)

    def get_file_name(self) -> str:
        """returns the name of the sdf file without the filepath attached to it"""
        # Filepath der Datei die eingelesen werden soll aufteilen, sodass nur der Dateiname übrig bleibt
        components = self.path.split("/")
        # nur filename zurückgeben
        return components[-1]

    def load_sdf(self, filepath: str):
        """loads the sdf-file. Gets called by __init__"""
        f = open(filepath)
        line = f.readline()
        data_array_created = False
        while line != "":
            d = line.split('=')
            if line.startswith('*') and not data_array_created:
                self.data['z'] = np.empty(shape=(self.data['numProfiles'],
                                                 self.data['numPoints']), dtype=float)
                data_array_created = True
                # read actual surface data
                line = f.readline()
                xpos = 0
                ypos = 0
                while not line.startswith('*') and line != "":
                    d = line.split()
                    for i in range(len(d)):
                        if d[i].startswith('BAD'):
                            self.data['z'][ypos][xpos] = float('nan')
                        else:
                            # multiply with 1000 to scale to um
                            self.data['z'][ypos][xpos] = float(d[i]) * self.data['zScale'] * 1e6
                        xpos += 1
                        if (xpos == self.data['numPoints']):
                            xpos = 0
                            ypos += 1
                    line = f.readline()
            elif d[0].startswith("NumPoints"):
                self.data['numPoints'] = int(d[1])
            elif d[0].startswith("NumProfiles"):
                self.data['numProfiles'] = int(d[1])
            elif d[0].startswith("Xscale"):
                self.data['xScale'] = float(d[1])
            elif d[0].startswith('Yscale'):
                self.data['yScale'] = float(d[1])
            elif d[0].startswith('Zscale'):
                self.data['zScale'] = float(d[1])
            line = f.readline()
        f.close()

    def interpolate_holes(self):
        def interpolate_missing_pixels(
                image: np.ndarray,
                mask: np.ndarray,
                method: str = 'nearest',
                fill_value: int = 0
        ):
            """
            :param image: a 2D image
            :param mask: a 2D boolean image, True indicates missing values
            :param method: interpolation method, one of
                'nearest', 'linear', 'cubic'.
            :param fill_value: which value to use for filling up data outside the
                convex hull of known pixel values.
                Default is 0, Has no effect for 'nearest'.
            :return: the image with missing values interpolated
            """
            from scipy import interpolate

            h, w = image.shape[:2]
            xx, yy = np.meshgrid(np.arange(w), np.arange(h))

            known_x = xx[~mask]
            known_y = yy[~mask]
            known_v = image[~mask]
            missing_x = xx[mask]
            missing_y = yy[mask]

            interp_values = interpolate.griddata(
                (known_x, known_y), known_v, (missing_x, missing_y),
                method=method, fill_value=fill_value
            )

            interp_image = image.copy()
            interp_image[missing_y, missing_x] = interp_values

            return interp_image
        self.data['z'] = interpolate_missing_pixels(self.data['z'], np.ma.masked_invalid(self.data['z']).mask)

    def get_z_value(self, x: float, y: float) -> float:
        """calculates the z-value to a value x or y and returns it. This includes the rotation of the surface around
        self.rotX and self.rotY by the angle self.phi. Instead of rotating the matrix, the point is rotated in the
        inverse direction. The unit is always um."""
        ox = self.rotX
        oy = self.rotY
        angle = -self.rotPhi/180*math.pi
        qx = ox + math.cos(angle) * (x - ox) - math.sin(angle) * (y - oy)
        qy = oy + math.sin(angle) * (x - ox) + math.cos(angle) * (y - oy)
        return self.interp(([qy], [qx]))[0]

    def plot_surface(self, fig, ax, width: float, number_of_surfaces: int, z_unit: int) -> None:
        """plots the surface from the sdf-file. Width: maximum width of the dxf-file, res: resolution of the ramp"""
        ax.set(xlabel='x', ylabel='y', zlabel='z')
        fig.tight_layout()

        # rotate the samples
        offset = [self.rotX, self.rotY, 0]
        a = self.rotPhi/180*math.pi
        array = np.array([self.data['x'], self.data['y'], self.data['z']])
        t = np.transpose(array, (1, 2, 0))
        # move the zero-point of the dxf file to the center of the coordinate system for the rotation
        t = t - offset
        # define the rotation matrix for a rotation around the z-axis
        m = [[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]]
        array = np.dot(t, m)
        # move the entire matrix back by the offset
        array = array + offset
        x, y, z = np.transpose(array, (2, 0, 1))
        # array = np.transpose(np.dot(t, m), (2, 0, 1))
        # x, y, z = array + offset

        surf = ax.plot_surface(x, y, z, cmap=cm.coolwarm, alpha=0.7)

        if not self.colorbarPlotted:
            fig.colorbar(surf, shrink=0.5, aspect = 5)
            self.colorbarPlotted = True

    def set_rotation(self, x0: float, y0: float, phi: float) -> None:
        self.rotX = x0
        self.rotY = y0
        self.rotPhi = phi
