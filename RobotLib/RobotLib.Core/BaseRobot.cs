using System;

namespace RobotLib
{
    /// <summary>
    /// 提供 OnLog 事件的基礎實作，讓各廠牌的 Robot 繼承
    /// </summary>
    public abstract class BaseRobot : IRobotActions
    {
        public event Action<string> OnLog;

        protected void RaiseLog(string msg)
        {
            OnLog?.Invoke(msg);
        }

        // 將方法宣告為 abstract，強制繼承者實作
        public abstract void MoveTo(int x, int y, int z);
        public abstract void Grab();
        public abstract void Release();
        public abstract void PrintNumbers();

        // --- 新增功能的抽象宣告 ---
        public abstract void ConnectRobot(string ipAddress, int port);
        public abstract void DisconnectRobot();
        public abstract void PowerOnServo();
        public abstract void PowerOffServo();
        public abstract void SetSpeed(int percentage);
        public abstract void SetAcceleration(int percentage);
        public abstract void MoveJoint(double j1, double j2, double j3, double j4, double j5, double j6);
        public abstract void MoveLinear(double x, double y, double z, double rx, double ry, double rz);
        public abstract void MoveCircular(CartesianPoint viaPoint, CartesianPoint endPoint);
        public abstract void StopMotion();
        public abstract void WaitForMoveFinish();
        public abstract double[] GetCurrentJointPosition();
        public abstract CartesianPoint GetCurrentCartesianPosition();
        public abstract string GetRobotStatus();
        public abstract void SetDigitalOutput(int port, bool value);
        public abstract bool GetDigitalInput(int port);
        public abstract void SetToolCoordinate(double[] toolData);
        public abstract void SetUserCoordinate(double[] userData);
    }
}
