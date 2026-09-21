# 2026-09-17

## 🏭 OpenClaw CAD Hybrid Agent Production Knowledge

### 系统架构

**当前生产架构：**

Ubuntu AI Server → OpenClaw Gateway → Win-CAD-Node → Windows AutoCAD 2020

Ubuntu AI Server 职责：AI 推理、Agent 任务规划、OpenClaw 运行
Win-CAD-Node 职责：Windows 执行、CUA 视觉、AutoCAD 环境

### Win-CAD-Node 状态

已完成生产化。
状态：paired=true, connected=true
Session: Interactive Desktop Session 2
Capabilities: screen, computer, browser, file, system

启动方式：Windows Task Scheduler, node.vbs 隐藏启动
重要：不要修改为 Windows Service，可能导致 computer 控制失效

### CUA 调试结论

已验证：screen.snapshot 成功，computer 能力正常，Notepad 测试成功
但是：AutoCAD 纯 GUI 控制不稳定，错误 DriverError.Tool
原因：AutoCAD 是专业图形软件，自绘界面，GPU 渲染
结论：不要强制使用纯鼠标键盘方式绘制 CAD

### AutoCAD 最终架构

采用：AutoCAD Hybrid Agent
流程：用户需求 → AI 理解 → CAD 任务规划 → CAD Executor → AutoCAD COM API → 生成 DWG/DXF → CUA 截图验证 → 返回结果

### CAD 控制优先级

优先：
1. AutoCAD COM API
2. AutoLISP
3. AutoCAD Script
4. accoreconsole

CUA 只负责：启动软件、查看状态、截图验证

### 已验证成功任务

测试：创建 1000×500 矩形，添加水平/垂直中心线，保存 CAD 文件
结果：AUTO CAD HYBRID AGENT READY
执行脚本：C:\Users\11561\Documents\AgnesCode\AutoCAD-Hybrid-Agent.ps1
输出文件：C:\OpenClaw-CAD-Test\Test.dxf.dwg

### Timeout 配置

Agent timeout: 600秒
Provider timeout: 900秒

### 后续 CAD 任务规则

禁止：直接纯鼠标绘图
必须：分析需求 → 生成 CAD 操作计划 → 调用 CAD Executor → 执行 AutoCAD → CUA 验证 → 保存文件 → 返回结果
