from typing import Optional, Union

from .base_component import BaseComponent
from .net import Net


class Schematic:
    def __init__(self) -> None:
        self._nets: dict[str, Net] = {}
        self._components: dict[str, BaseComponent] = {}
        self._frozen = False

        self._anon_net_counter = 0

    @property
    def nets(self):
        return tuple(self._nets.values())

    @property
    def components(self):
        return tuple(self._components.values())

    @property
    def frozen(self):
        return self._frozen

    def _resolve_component(self, comp: Union[str, BaseComponent]) -> BaseComponent:
        if isinstance(comp, str):
            return self.component(comp)

        if isinstance(comp, BaseComponent):
            if comp.name not in self._components:
                raise KeyError(f"Component '{comp.name}' not registered in schematic")

            return self._components[comp.name]
        raise TypeError("component must be a name (str) or BaseComponent")

    def _new_auto_net_name(self) -> str:
        self._anon_net_counter += 1
        return f"N${self._anon_net_counter}"

    def _merge_nets(self, net_target: Net, net_source: Net) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")

        if net_target is net_source:
            return

        # Move all connections from source to target
        for component, pin_set in list(net_source._connections.items()):
            for pin_idx in pin_set:
                pin = component.pins[pin_idx]

                # REMOVE pin from source net
                pin.net = None

                # ADD pin to target net WITHOUT using Net.connect()
                net_target._connections.setdefault(component, set()).add(pin_idx)
                pin.net = net_target

        # Remove source net from schematic registry
        del self._nets[net_source.name]

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

    def component(self, name: str) -> BaseComponent:
        try:
            return self._components[name]
        except KeyError:
            raise KeyError(f"Unknown component '{name}'")

    def connect(self, net: str, component: str, pin: int | str) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")
        self.net(net).connect(self.component(component), pin)

    def connect_create_net(self, net_name: str, component: str, pin: int | str) -> None:
        if self._frozen:
            raise RuntimeError("Schematic is frozen")
        if net_name not in self._nets:
            self.add_net(Net(net_name))
        self.connect(net_name, component, pin)

    def connect_pins(
        self,
        comp_a: Union[str, BaseComponent],
        pin_a: int | str,
        comp_b: Union[str, BaseComponent],
        pin_b: int | str,
        *,
        net_name: Optional[str] = None,
        allow_merge: bool = False,
    ) -> Net:
        """
        Connect pin A and pin B together. Behavior:
        - if both pins unconnected -> create new net (named by net_name or auto-name) and attach both
        - if one pin has a net -> attach the other pin to that net
        - if both pins are on same net -> no-op, return that net
        - if both pins are on different nets:
            - if allow_merge True -> merge the nets (net_b -> net_a) and return merged net
            - else -> raise ValueError (require explicit merge)
        """
        if self._frozen:
            raise RuntimeError("Schematic is frozen")

        a = self._resolve_component(comp_a)
        b = self._resolve_component(comp_b)

        p_a = a.pin(pin_a) if isinstance(pin_a, str) else a.pins[pin_a]
        p_b = b.pin(pin_b) if isinstance(pin_b, str) else b.pins[pin_b]

        net_a = p_a.net
        net_b = p_b.net

        # Case: both unconnected -> create new net
        if net_a is None and net_b is None:
            chosen_name = net_name or self._new_auto_net_name()
            if chosen_name in self._nets:
                net = self._nets[chosen_name]
            else:
                net = Net(chosen_name)
                self.add_net(net)
            net.connect(a, p_a.index)
            net.connect(b, p_b.index)
            return net

        # Case: one side connected -> attach other
        if net_a is not None and net_b is None:
            net_a.connect(b, p_b.index)
            return net_a
        if net_b is not None and net_a is None:
            net_b.connect(a, p_a.index)
            return net_b

        # Case: both connected
        if net_a is net_b:
            return net_a

        # different nets -> require explicit merge
        if not allow_merge:
            raise ValueError(
                f"Pins are on different nets ('{net_a.name}' != '{net_b.name}');"
                " pass allow_merge=True to merge explicitly"
            )

        # merge net_b into net_a (keep net_a's name)
        self._merge_nets(net_target=net_a, net_source=net_b)
        return net_a

    def freeze(self):
        self._frozen = True

    def ground(self) -> Net:
        grounds = [n for n in self._nets.values() if n.is_ground]
        if not grounds:
            raise ValueError("No ground net defined")
        if len(grounds) > 1:
            raise ValueError("Multiple ground nets defined")
        return grounds[0]

    def validate(self) -> None:
        for c in self._components.values():
            for p in c.pins:
                if p.net is None:
                    raise ValueError(
                        f"Component {c.name} has unconnected pin '{p.name}'"
                    )
