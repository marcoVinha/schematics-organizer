from typing import Callable, Optional

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class VoltageSource(BaseComponent):
    def __init__(self, name: str, voltage: float | Callable):
        super().__init__(
            name=name,
            pin_names=["+", "-"],
            parameters={"voltage": voltage},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.VOLTAGE_SOURCE
