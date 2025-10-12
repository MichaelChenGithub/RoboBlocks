"""Simple computer vision scaffold for Blockly-generated programs."""
from __future__ import annotations


class CVModel:
    def __init__(self) -> None:
        print("[CVModel] instance created")

    def create_model(self) -> None:
        print("[CVModel] create_model")

    def set_hyperparams(self, a, b, c) -> None:
        print(f"[CVModel] set_hyperparams a={a} b={b} c={c}")
