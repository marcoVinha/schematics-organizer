from typing import Optional

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class NPNTransistor(BaseComponent):
    def __init__(self, name: str, beta: float, part_number: Optional[str]):
        super().__init__(
            name=name,
            pin_names=["collector", "base", "emitter"],
            parameters={"base_type": "npn", "beta": beta, "part_number": part_number},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.BJT
