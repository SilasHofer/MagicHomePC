import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .bulb_service import BulbService
from .models import BrightnessUpdate, ColorUpdate, Device, DeviceCheck, DeviceCreate, DeviceState
from .repository import DeviceRepository

repository = DeviceRepository(os.getenv("DEVICES_DB", "data/devices.db"))
service = BulbService(repository)

app = FastAPI(title="Magic Home Control API", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def service_error(error: Exception, ip: str) -> HTTPException:
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return HTTPException(
            status_code=504,
            detail=f"Bulb at {ip} is unreachable. Check that it is powered on and that its IP address is correct.",
        )
    return HTTPException(status_code=502, detail=f"Bulb communication failed: {error}")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/devices", response_model=list[Device])
def list_devices() -> list[Device]:
    return repository.list()


@app.post("/api/devices", response_model=Device, status_code=201)
def add_device(device: DeviceCreate) -> Device:
    try:
        if not service.check(device.ip):
            raise HTTPException(status_code=502, detail="The device did not respond")
        return repository.add(Device(**device.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise service_error(error, device.ip) from error


@app.post("/api/devices/check")
def check_device(device: DeviceCheck) -> dict[str, bool]:
    try:
        return {"reachable": service.check(device.ip)}
    except Exception as error:
        raise service_error(error, device.ip) from error


@app.delete("/api/devices/{ip}", status_code=204)
def delete_device(ip: str) -> None:
    if not repository.remove(ip):
        raise HTTPException(status_code=404, detail="Device not found")


@app.post("/api/devices/all/{action}")
def set_all(action: str) -> dict[str, list[str]]:
    if action not in {"on", "off"}:
        raise HTTPException(status_code=400, detail="Action must be on or off")
    failed = service.set_all([device.ip for device in repository.list()], action == "on")
    return {"failed": failed}


@app.get("/api/devices/{ip}/state", response_model=DeviceState)
def get_state(ip: str) -> DeviceState:
    try:
        return service.state(ip)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise service_error(error, ip) from error


@app.post("/api/devices/{ip}/on", status_code=204)
def turn_on(ip: str) -> None:
    try:
        service.turn_on(ip)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise service_error(error, ip) from error


@app.post("/api/devices/{ip}/off", status_code=204)
def turn_off(ip: str) -> None:
    try:
        service.turn_off(ip)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise service_error(error, ip) from error


@app.put("/api/devices/{ip}/color", status_code=204)
def set_color(ip: str, color: ColorUpdate) -> None:
    try:
        service.set_color(ip, color.red, color.green, color.blue)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise service_error(error, ip) from error


@app.put("/api/devices/{ip}/brightness", status_code=204)
def set_brightness(ip: str, brightness: BrightnessUpdate) -> None:
    try:
        service.set_brightness(ip, brightness.brightness)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise service_error(error, ip) from error
