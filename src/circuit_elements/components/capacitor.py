from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class Capacitor(BaseComponent):
    def __init__(self, name: str, capacitance_farad: float):
        super().__init__(
            name=name,
            pin_names=["a", "b"],
            parameters={"capacitance": capacitance_farad},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.CAPACITOR
