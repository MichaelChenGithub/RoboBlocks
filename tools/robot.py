"""Simple runtime scaffolding for Blockly-generated programs."""
from __future__ import annotations

from typing import Any, Iterable, Tuple


def _format_iterable(values: Iterable[Any]) -> str:
    return ", ".join(str(v) for v in values)


class RobotAction:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def connect_robot(self, ip, *, port=60008, timeout_ms=0) -> None:
        print(f"[Robot] connect_robot ip={ip} port={port} timeout_ms={timeout_ms}")

    def disconnect(self) -> None:
        print("[Robot] disconnect")

    def power_on_servo(self) -> None:
        print("[Robot] power_on_servo")

    def power_off_servo(self) -> None:
        print("[Robot] power_off_servo")


class RobotMotion:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def set_speed(self, percentage: float) -> None:
        print(f"[Robot] set_speed {percentage}%")

    def set_acceleration(self, percentage: float) -> None:
        print(f"[Robot] set_acceleration {percentage}%")

    def move_to(self, x: float, y: float, z: float, *, speed: float | None = None) -> None:
        speed_str = f" speed={speed}" if speed is not None else ""
        print(f"[Robot] move_to x={x} y={y} z={z}{speed_str}")

    def move_joint(self, *joints: float, speed: float | None = None) -> None:
        joints_str = _format_iterable(joints)
        speed_str = f" speed={speed}" if speed is not None else ""
        print(f"[Robot] move_joint joints=({joints_str}){speed_str}")

    def move_linear(self, *axes: float, speed: float | None = None) -> None:
        axes_str = _format_iterable(axes)
        speed_str = f" speed={speed}" if speed is not None else ""
        print(f"[Robot] move_linear axes=({axes_str}){speed_str}")

    def move_circular(self, *, via: Tuple[float, ...], end: Tuple[float, ...]) -> None:
        print(
            f"[Robot] move_circular via=({_format_iterable(via)}) end=({_format_iterable(end)})"
        )

    def stop(self, stop_type: str | None = None) -> None:
        suffix = f" type={stop_type}" if stop_type else ""
        print(f"[Robot] stop{suffix}")

    def wait_for_finish(self, timeout_ms: float | None = None) -> None:
        suffix = f" timeout_ms={timeout_ms}" if timeout_ms else ""
        print(f"[Robot] wait_for_finish{suffix}")


class RobotFrames:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def set_tool(self, *coords: float) -> None:
        print(f"[Robot] set_tool coords=({_format_iterable(coords)})")

    def set_user(self, *coords: float) -> None:
        print(f"[Robot] set_user coords=({_format_iterable(coords)})")


class RobotGripper:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def grab(self) -> None:
        print("[Robot] gripper.grab")

    def release(self) -> None:
        print("[Robot] gripper.release")


class RobotDebug:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def print_numbers(self) -> None:
        print("[Robot] debug.print_numbers")


class RobotStatus:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def joint_position(self):
        print("[Robot] status.joint_position")
        return (0, 0, 0, 0, 0, 0)

    def cartesian_position(self):
        print("[Robot] status.cartesian_position")
        return {"x": 0, "y": 0, "z": 0}

    def snapshot(self):
        print("[Robot] status.snapshot")
        return {"state": "ok"}


class RobotIO:
    def __init__(self, robot: "Robot") -> None:
        self._robot = robot

    def set_output(self, port: int, value: bool) -> None:
        print(f"[Robot] io.set_output port={port} value={value}")

    def get_input(self, port: int) -> bool:
        print(f"[Robot] io.get_input port={port}")
        return False


class Robot:
    def __init__(self) -> None:
        self.action = RobotAction(self)
        self.motion = RobotMotion(self)
        self.frames = RobotFrames(self)
        self.gripper = RobotGripper(self)
        self.debug = RobotDebug(self)
        self.status = RobotStatus(self)
        self.io = RobotIO(self)
        self.brand = "default"

        print("[Robot] instance created")
