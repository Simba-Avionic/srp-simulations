from dataclasses import dataclass
from someipy.serialization import (
    Float32,
)

class PressCalibrationRes:
    def __init__(self):
        self.a = Float32()
        self.b = Float32()

    def from_json(self, json_obj):
        self.a.value = float(json_obj['a'])
        self.b.value = float(json_obj['b'])

    def serialize(self) -> bytes:
        return self.a.serialize() + self.b.serialize()

class GPSDataStructure:
    def __init__(self):
        self.latitude = Float32()
        self.longitude = Float32()
        self.altitude = Float32()

    def from_json(self, json_obj):
        self.latitude.value = float(json_obj['latitude'])
        self.longitude.value = float(json_obj['longitude'])
        self.altitude.value = float(json_obj['altitude'])

    def serialize(self) -> bytes:
        return self.latitude.serialize() + self.longitude.serialize() + self.altitude.serialize()