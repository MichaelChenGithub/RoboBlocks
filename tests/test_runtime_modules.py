import io
import unittest
from contextlib import redirect_stdout

from tools.robot import Robot
from tools.vision import CVModel


class RobotRuntimeTests(unittest.TestCase):
    def capture(self, func, *args, **kwargs):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = func(*args, **kwargs)
        return buffer.getvalue(), result

    def test_robot_methods_emit_output(self):
        robot_output, robot = self.capture(Robot)
        self.assertIn("instance created", robot_output)

        out, _ = self.capture(robot.action.connect_robot, "192.168.0.1", port=1234, timeout_ms=1000)
        self.assertIn("connect_robot", out)

        out, _ = self.capture(robot.motion.move_to, 1, 2, 3, speed=50)
        self.assertIn("move_to", out)

        out, status = self.capture(robot.status.snapshot)
        self.assertIn("snapshot", out)
        self.assertIsInstance(status, dict)

        out, value = self.capture(robot.io.get_input, 5)
        self.assertIn("io.get_input", out)
        self.assertFalse(value)

    def test_cv_model_methods_emit_output(self):
        model_output, model = self.capture(CVModel)
        self.assertIn("instance created", model_output)

        out, _ = self.capture(model.create_model)
        self.assertIn("create_model", out)

        out, _ = self.capture(model.set_hyperparams, 1, 2, 3)
        self.assertIn("set_hyperparams", out)


if __name__ == "__main__":
    unittest.main()
