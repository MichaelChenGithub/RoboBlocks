using System;

namespace RobotLib
{
    /// <summary>
    /// 代表一個包含位置和姿態的笛卡爾座標點
    /// </summary>
    public class CartesianPoint
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
        public double Rx { get; set; }
        public double Ry { get; set; }
        public double Rz { get; set; }

        public override string ToString()
        {
            return $"({X}, {Y}, {Z}, {Rx}, {Ry}, {Rz})";
        }
    }

    /// <summary>
    /// 定義所有機械手臂共通的介面
    /// </summary>
    public interface IRobotActions
    {
        /// <summary>
        /// 當有日誌訊息產生時觸發
        /// </summary>
        event Action<string> OnLog;

        /// <summary>
        /// 移動到指定座標
        /// </summary>
        void MoveTo(int x, int y, int z);

        /// <summary>
        /// 執行抓取
        /// </summary>
        void Grab();

        /// <summary>
        /// 執行釋放
        /// </summary>
        void Release();

        /// <summary>
        /// 打印數字 (測試用)
        /// </summary>
        void PrintNumbers();

        // --- 新增功能 ---

        void ConnectRobot(string ipAddress, int port);
        void DisconnectRobot();
        void PowerOnServo();
        void PowerOffServo();
        void SetSpeed(int percentage);
        void SetAcceleration(int percentage);
        void MoveJoint(double j1, double j2, double j3, double j4, double j5, double j6);
        void MoveLinear(double x, double y, double z, double rx, double ry, double rz);
        void MoveCircular(CartesianPoint viaPoint, CartesianPoint endPoint);
        void StopMotion();
        void WaitForMoveFinish();
        double[] GetCurrentJointPosition();
        CartesianPoint GetCurrentCartesianPosition();
        string GetRobotStatus();
        void SetDigitalOutput(int port, bool value);
        bool GetDigitalInput(int port);
        void SetToolCoordinate(double[] toolData);
        void SetUserCoordinate(double[] userData);
    }
}
