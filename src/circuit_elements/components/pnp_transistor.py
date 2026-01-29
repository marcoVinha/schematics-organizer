from typing import Optional

from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class PNPTransistor(BaseComponent):
    def __init__(self, name: str, beta: float, part_number: Optional[str]):
        super().__init__(
            name=name,
            pin_names=["emitter", "base", "collector"],
            parameters={"base_type": "pnp", "beta": beta, "part_number": part_number},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.BJT
