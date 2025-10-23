# Blockly 機器人程式產生器

## 專案簡介
本專案提供一個基於 PyQt6 的桌面應用程式，讓使用者透過 Blockly 積木設計機器人流程並即時產生對應的 Python 程式碼。Qt WebEngine 會載入 `pyqt_app/resources/blockly_app.html`，前端再透過 `RobotCompilerBridge` 將程式碼推回 `pyqt_app/main.py` 的程式碼檢視器與終端面板。內建背景執行器 (`pyqt_app/executor.py`) 可直接在工具內執行與除錯產生的腳本。

## 系統需求與環境安裝
1. 安裝 Python 3.10 以上版本（建議 3.11），並確認 `python3 --version` 可以正常顯示版本號。
2. 取得專案原始碼並切換到根目錄：
   ```bash
   git clone <repository-url>
   cd Codey
   ```
3. 建立虛擬環境並安裝相依套件：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows 請改用 .\.venv\Scripts\activate
   pip install --upgrade pip
   pip install PyQt6 PyQt6-WebEngine
   ```
   - `PyQt6` 提供桌面元件；`PyQt6-WebEngine` 使 `QWebEngineView` 能嵌入 Blockly 網頁。
   - 若計畫在 Linux 上執行，請先確認系統已安裝 Qt WebEngine 需要的系統套件（例如 `libxcb`、`mesa` 等）。
4. 專案已內建離線的 Blockly 套件 (`pyqt_app/resources/vendor/blockly`)，首次啟動無須額外建置前端資產。

## 執行桌面應用
在啟用的虛擬環境中於專案根目錄執行：
```bash
python -m pyqt_app.main
```
程式會開啟一個含有 Blockly 工作區、Python 程式檢視器與終端輸出窗格的視窗。**Save Python...** 會輸出目前腳本（預設檔名為 `generated_workflow.py`），**Run** 則會呼叫 `PythonExecutionWorker` 以背景執行當前程式碼並將輸出印在終端區塊。

## 測試
專案測試採用標準 `unittest`：
```bash
python -m unittest
```
測試涵蓋 Qt 溝通橋 (`tests/test_bridge.py`) 與工具層 (`tests/test_runtime_modules.py`)，可協助確認擴充後的功能仍維持正確。

## 專案結構
- `pyqt_app/main.py`：Qt 主視窗、工具列與背景執行流程。
- `pyqt_app/bridge.py`：前端透過 WebChannel 呼叫的橋接介面。
- `pyqt_app/executor.py`：在背景執行 Blockly 產生的 Python 程式。
- `pyqt_app/resources/`：前端 HTML、Blockly toolbox 及產碼器腳本與離線 vendor 檔案。
- `tools/`：提供給產生程式引用的 Python runtime（目前包含 `Robot` 與 `CVModel`）。
- `tests/`：針對橋接層與工具層的單元測試。

## 新增 tools 工具流程（詳細）
以下示範如何新增一個可被 Blockly 程式碼使用的工具，例如 `Gripper`：

1. **建立執行模組**  
   在 `tools/` 底下新增模組檔並實作對應的類別與方法，例如：
   ```python
   # tools/gripper.py
   class Gripper:
       def __init__(self) -> None:
           print("[Gripper] instance created")

       def open(self) -> None:
           print("[Gripper] open")

       def close(self) -> None:
           print("[Gripper] close")
   ```
2. **匯出模組供產生器引用**  
   更新 `tools/__init__.py`，把新模組加入 `__all__`，讓 `from tools.gripper import Gripper` 可以運作。
3. **擴充 Python 產碼器** (`pyqt_app/resources/robot_python_generator.js`)  
   - 在 `python.addReservedWords` 加上新的工具變數名稱，避免 Blockly 產生的程式碼覆寫它。  
   - 參考 `ensureCvModelRuntime` 的寫法新增 `ensureGripperRuntime`，為 Python 產碼加入匯入與單例建立：
     ```javascript
     function ensureGripperRuntime() {
         python.definitions_ = python.definitions_ || Object.create(null);
         if (!python.definitions_['import_gripper']) {
             python.definitions_['import_gripper'] = 'from tools.gripper import Gripper';
         }
         if (!python.definitions_['gripper_instance']) {
             python.definitions_['gripper_instance'] = 'gripper = Gripper()';
         }
     }
     ```
   - 在對應方塊的產碼函式中呼叫 `ensureGripperRuntime()` 並使用既有的 `statement(...)` helper 或自行回傳字串。例如：
     ```javascript
     python.forBlock['gripper_open'] = function(block) {
         ensureGripperRuntime();
         return 'gripper.open()\n';
     };
     ```
4. **新增 Blockly 方塊** (`pyqt_app/resources/robot_blocks.js`)  
   - 依需求將新方塊加入既有分類（如 `CATEGORY_ACTIONS`），或建立新的分類物件並把它加入 `Blockly.RobotToolbox` 的 `contents` 陣列。  
   - 使用 `createBlock`／`addNumberField`／`addTextField` 等 helper 定義方塊 UI，並確保 `type` 名稱與第三步的 `python.forBlock[...]` 相符。
5. **重新啟動桌面程式並驗證**  
   重新啟動 `python -m pyqt_app.main`，在 Blockly 中拖曳新方塊，確認左側 Python 面板與執行輸出都能正確呼叫新工具。
6. **補齊測試**  
   依照 `tests/test_runtime_modules.py` 的模式撰寫新的單元測試，確保新工具方法會輸出預期訊息並返回正確值。

完成以上步驟後，新工具就能在 Blockly 工作區中使用，而且產生的 Python 腳本會自動加入匯入與實例初始化。

## 常見疑難排查
- **Qt WebEngine 無法載入**：請確認已安裝 `PyQt6-WebEngine`，並在 Linux 上安裝所需的系統套件。
- **前端修改沒有生效**：若在程式執行時修改 `robot_blocks.js` 或 `robot_python_generator.js`，請完全關閉應用程式並重新啟動，讓 Qt WebEngine 重新載入檔案。
