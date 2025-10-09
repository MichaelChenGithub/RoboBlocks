using System;
using RobotLib;

namespace GeneratedWorkflows
{
    public static class RobotProgram
    {
        public static void Run()
        {
            var robot = new FanucRobot();
            // timeout_ms: 5000
            robot.ConnectRobot("192.168.0.10", 60008);
            robot.DisconnectRobot();
        }
    }
}