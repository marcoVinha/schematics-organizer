from .base_component import BaseComponent
from .net import Net


class Schematic:
    def __init__(self) -> None:
        self._nets: dict[str, Net] = {}
        self._components: dict[str, BaseComponent] = {}
        self._frozen = False

    @property
    def nets(self):
        return tuple(self._nets.values())

    @property
    def components(self):
        return tuple(self._components.values())

    @property
    def frozen(self):
        return self._frozen

    def add_net(self, net: Net) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")
        if net.name in self._nets:
            raise ValueError(f"Net '{net.name}' already exists")
        self._nets[net.name] = net

    def add_component(self, component: BaseComponent) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")

        if component.name in self._components:
            raise ValueError(f"Component '{component.name}' already exists")

        self._components[component.name] = component

    def net(self, name: str) -> Net:
        try:
            return self._nets[name]
        except KeyError:
            raise KeyError(f"Unknown net '{name}'")

    def connect(self, net: str, component: str, pin: int | str) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")
        self.net(net).connect(self.component(component), pin)

    def freeze(self):
        self._frozen = True

    def ground(self) -> Net:
        grounds = [n for n in self._nets.values() if n.is_ground]
        if not grounds:
            raise ValueError("No ground net defined")
        if len(grounds) > 1:
            raise ValueError("Multiple ground nets defined")
        return grounds[0]
