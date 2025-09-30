using System;
using System.Threading;

namespace RobotLib
{
    /// <summary>
    /// 預設的機械手臂實作
    /// </summary>
    public class DefaultRobot : BaseRobot
    {
        public override void PrintNumbers()
        {
            for (int i = 1; i <= 5; i++)
            {
                RaiseLog(string.Format("DefaultRobot Number: {0}", i));
                Thread.Sleep(300);
            }
        }

        public override void MoveTo(int x, int y, int z)
        {
            RaiseLog(string.Format("DefaultRobot Moving to position ({0},{1},{2})", x, y, z));
        }

        public override void Grab()
        {
            RaiseLog("DefaultRobot Grabbing object");
        }

        public override void Release()
        {
            RaiseLog("DefaultRobot Releasing object");
        }

        // --- 新增功能的實作 ---
        public override void ConnectRobot(string ipAddress, int port)
        {
            RaiseLog($"DefaultRobot ConnectRobot: ip_address={ipAddress}, port={port}");
        }

        public override void DisconnectRobot()
        {
            RaiseLog("DefaultRobot DisconnectRobot");
        }

        public override void PowerOnServo()
        {
            RaiseLog("DefaultRobot PowerOnServo");
        }

        public override void PowerOffServo()
        {
            RaiseLog("DefaultRobot PowerOffServo");
        }

        public override void SetSpeed(int percentage)
        {
            RaiseLog($"DefaultRobot SetSpeed: percentage={percentage}");
        }

        public override void SetAcceleration(int percentage)
        {
            RaiseLog($"DefaultRobot SetAcceleration: percentage={percentage}");
        }

        public override void MoveJoint(double j1, double j2, double j3, double j4, double j5, double j6)
        {
            RaiseLog($"DefaultRobot MoveJoint: j1={j1}, j2={j2}, j3={j3}, j4={j4}, j5={j5}, j6={j6}");
        }

        public override void MoveLinear(double x, double y, double z, double rx, double ry, double rz)
        {
            RaiseLog($"DefaultRobot MoveLinear: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}");
        }

        public override void MoveCircular(CartesianPoint viaPoint, CartesianPoint endPoint)
        {
            RaiseLog($"DefaultRobot MoveCircular: via_point={viaPoint}, end_point={endPoint}");
        }

        public override void StopMotion()
        {
            RaiseLog("DefaultRobot StopMotion");
        }

        public override void WaitForMoveFinish()
        {
            RaiseLog("DefaultRobot WaitForMoveFinish");
        }

        public override double[] GetCurrentJointPosition()
        {
            RaiseLog("DefaultRobot GetCurrentJointPosition");
            return new double[] { 0, 0, 0, 0, 0, 0 };
        }

        public override CartesianPoint GetCurrentCartesianPosition()
        {
            RaiseLog("DefaultRobot GetCurrentCartesianPosition");
            return new CartesianPoint { X = 0, Y = 0, Z = 0, Rx = 0, Ry = 0, Rz = 0 };
        }

        public override string GetRobotStatus()
        {
            RaiseLog("DefaultRobot GetRobotStatus");
            return "Idle";
        }

        public override void SetDigitalOutput(int port, bool value)
        {
            RaiseLog($"DefaultRobot SetDigitalOutput: port={port}, value={value}");
        }

        public override bool GetDigitalInput(int port)
        {
            RaiseLog($"DefaultRobot GetDigitalInput: port={port}");
            return false;
        }

        public override void SetToolCoordinate(double[] toolData)
        {
            RaiseLog($"DefaultRobot SetToolCoordinate: toolData={string.Join(",", toolData)}");
        }

        public override void SetUserCoordinate(double[] userData)
        {
            RaiseLog($"DefaultRobot SetUserCoordinate: userData={string.Join(",", userData)}");
        }
    }
}
