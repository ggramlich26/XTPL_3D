from abc import ABC, abstractmethod


class Surface(ABC):
    @abstractmethod
    def get_z_value(self, x: float, y: float) -> float:
        pass

    @abstractmethod
    def get_file_name(self) -> str:
        pass

    @abstractmethod
    def plot_surface(self, fig, ax, width: float, number_of_surfaces: int, z_unit: int) -> None:
        pass

    @abstractmethod
    def set_rotation(self, x0:float, y0:float, phi:float) -> None:
        pass