from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class Potentiometer(BaseComponent):
    def __init__(self, name: str, resistance_ohm: float):
        super().__init__(
            name=name,
            pin_names=["1", "2", "3"],
            parameters={"resistance": resistance_ohm},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.POTENTIOMETER
