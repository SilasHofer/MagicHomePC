from typing import Literal

from pydantic import BaseModel, Field


class Device(BaseModel):
    name: str
    ip: str
    type: str
    color_order: str


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    ip: str = Field(min_length=7, max_length=45)
    type: str = "Flux"
    color_order: Literal["RGB", "GRB", "BGR", "GBR", "RBG", "BRG"] = "RGB"


class DeviceCheck(BaseModel):
    ip: str = Field(min_length=7, max_length=45)


class ColorUpdate(BaseModel):
    red: int = Field(ge=0, le=255)
    green: int = Field(ge=0, le=255)
    blue: int = Field(ge=0, le=255)


class BrightnessUpdate(BaseModel):
    brightness: int = Field(ge=0, le=100)


class DeviceState(BaseModel):
    ip: str
    is_on: bool
    color: tuple[int, int, int]
    brightness: int
