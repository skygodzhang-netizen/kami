# OpenClaw CAD Hybrid Agent Production State

> 写入时间：2026-09-17。用途：Gateway 重启 / Agent 重新加载 / 新会话启动后，快速恢复当前 CAD 架构、调试结论与工作方式。

## 系统架构

当前架构链路：

```
Ubuntu AI Server (192.168.100.108)
  ↓
OpenClaw Gateway
  ↓
Win-CAD-Node (192.168.100.109, IP 见节点登记)
  ↓
Windows AutoCAD 2020
```

- Ubuntu AI 负责：AI 推理、任务规划、Agent 执行
- Win-CAD-Node 负责：Windows 执行、CUA 视觉、AutoCAD 环境

## Win-CAD-Node 状态

当前生产状态：

- paired ✅
- connected ✅
- Session: Interactive Desktop Session 2

Capabilities:

- screen ✅
- computer ✅
- browser ✅
- file ✅
- system ✅

启动方式：

- Windows Task Scheduler
- node.vbs 隐藏启动

⚠️ 禁止改为 Windows Service。原因：Service 可能导致 screen 正常但 computer 失效。

## CUA 结论（已验证）

- screen.snapshot ✅
- computer 能力 ✅
- Notepad 控制 ✅

但是：AutoCAD 纯 GUI 鼠标键盘控制不稳定。

原因：AutoCAD 属于复杂专业软件：

- 自绘界面
- GPU 渲染
- 输入层复杂

因此：不要默认使用纯 CUA 绘图。

## CAD 最终方案

采用：AutoCAD Hybrid Agent。流程：

```
用户需求
  ↓
AI 理解
  ↓
CAD 规划
  ↓
CAD Executor
  ↓
COM API / AutoLISP / Script
  ↓
AutoCAD 执行
  ↓
CUA 截图验证
  ↓
输出 DWG/DXF
```

## CAD 控制优先级

以后 CAD 任务优先顺序：

1. AutoCAD COM API
2. AutoLISP
3. Script
4. accoreconsole

CUA 用途：

- 启动软件
- 查看状态
- 验证结果

不是主要绘图方式。

## 已验证能力

测试：1000×500 矩形、添加水平/垂直中心线、保存 CAD 文件。

结果：AUTO CAD HYBRID AGENT READY ✅

已确认：

- AutoCAD 自动启动 ✅
- CAD 命令执行 ✅
- 图形生成 ✅
- CUA 验证 ✅
- 文件生成 ✅

## Timeout 经验

之前问题：Request timed out before a response was generated。

原因：Provider timeout 不足。

当前：

- Agent timeout: 600s
- Provider timeout: 900s

以后排查长任务必须检查：

1. Agent timeout
2. Provider timeout
3. Tool timeout
4. Node timeout

## 后续行为规则

收到 CAD 任务时：

- 不要直接模拟鼠标绘图

必须：

1. 分析需求
2. 制定 CAD 动作计划
3. 调用 CAD Executor
4. 执行 AutoCAD
5. CUA 验证
6. 保存文件
7. 返回结果
