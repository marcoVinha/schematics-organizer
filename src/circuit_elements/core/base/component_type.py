from enum import Enum


class ComponentType(str, Enum):
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    BJT = "bjt"
    MOSFET = "mosfet"
    JFET = "jfet"
    OPAMP = "opamp"
    POTENTIOMETER = "potentiometer"
    TRANSFORMER = "transformer"
    IC = "ic"
