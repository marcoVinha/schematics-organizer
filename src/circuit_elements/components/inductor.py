from circuit_elements.core.base.base_component import BaseComponent
from circuit_elements.core.base.component_type import ComponentType


class Inductor(BaseComponent):
    def __init__(self, name: str, inductance_henry: float):
        super().__init__(
            name=name,
            pin_names=["a", "b"],
            parameters={"inductance": inductance_henry},
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.INDUCTOR
