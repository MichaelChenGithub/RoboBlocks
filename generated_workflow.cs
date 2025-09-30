using System;
using RobotLib;

namespace GeneratedWorkflows
{
    public static class RobotProgram
    {
        public static void Run()
        {
            var robot = new FanucRobot();
            robot.OnLog += message => Console.WriteLine(message);
            // timeout_ms: 5000
            robot.ConnectRobot("192.168.0.10", 60008);
            robot.PowerOnServo();
            robot.SetSpeed(75);
            // Move above the part
            // speed_percentage override: 40
            robot.MoveLinear(250, 150, 120, 0, 180, 90);
            robot.Grab();
            robot.MoveLinear(360, -120, 80, 0, 180, 0);
            robot.Release();
            // stop_type: normal
            robot.StopMotion();
            robot.DisconnectRobot();
        }
    }
}