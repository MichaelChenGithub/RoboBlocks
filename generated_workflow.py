from tools.robot import Robot
from tools.vision import CVModel

new_robot = Robot()

cv_model = CVModel()


def main():
  if False:
    new_robot.brand = "default"
    new_robot.action.connect_robot("192.168.0.10", port=60008, timeout_ms=5000)
    new_robot.action.disconnect()
    cv_model.create_model()
  new_robot.motion.set_speed(50)

if __name__ == "__main__":
    main()
