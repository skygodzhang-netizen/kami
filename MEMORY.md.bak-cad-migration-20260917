# 长期记录

- Tailscale serve 配置存在于 iStoreOS 路由器（`_serve/e416`），已观察到但不主动操作
- ✅ 2026-08-04: Google 账户安全异常 — 06:41-06:42 UTC 2FA 电话号码先添加后删除，疑似账户被盗迹象，需用户确认
- ✅ 2026-08-05: kami 确认上述 Google 安全警报为其本人操作（修改 2FA 手机号），非异常
- ✅ 2026-08-20: Git 推送完成，26 文件含巡检数据与记忆文件
- ✅ 2026-08-20: ElevenLabs TTS API Key 配置完成 (Free tier, 10K字符/月)
- ✅ 2026-08-20: Home Assistant 长期 access token 已配置并验证

---

# 2026-08-01

## 📈 投资日报

### 基金表现

- **016453 南方纳斯达克100指数(QDII)C**
  - 最新净值: 2.1115 (7月30日)
  - 今日估算: 涨跌待晚间确认
  - 近一季累计收益: -1.11%

---

### 市场

- **NASDAQ 100 (NDX)**: 28,274.195 (8月1日收盘)
- **美元人民币**: 6.75 - 6.77 (相对稳固)
- **科技股**:
  - NVDA: 目标价 $316.79，共识评级买入
  - MSFT: 7月31日大涨 +15.51%，受云/AI财报推动
  - AAPL: 目标价 $304.26，分析师看好

---

### 新闻影响

**利好:**
- 纳指单日飙升680点，创近期最大涨幅
- 微软云业务超预期，验证AI需求
- 科技股Q2财报整体好于预期

**风险:**
- 科技板块内部预期撕裂，软件/云情绪偏弱
- AI商业化落地仍需时间验证
- 美股科技股估值仍偏高

---

### 风险提示

近期科技股波动加大，Q2财报季为AI投入回报关键验证期。建议关注8月初后续财报数据，谨慎持有。

---

# 2026-08-06

## GitHub Token 配置
- 2026-08-06: 配置 GitHub PAT token 用于 workspace git 操作
- 远程仓库: skygodzhang-netizen/kami
- 完成首次推送，包含配置文件和脚本

---

# 2026-09-17

## CAD Hybrid Agent 生产状态 <!-- project: github.com/skygodzhang-netizen/kami -->
- Win-CAD-Node (192.168.100.109) 生产在线：paired/connected，screen/computer/browser/file/system 能力全注册；Task Scheduler + node.vbs 隐藏启动（禁止改 Service，会导致 computer 失效）
- 架构：Ubuntu AI Server → OpenClaw Gateway → Win-CAD-Node → Windows AutoCAD 2020
- CUA 验证结论：screen.snapshot/computer 可用（Notepad 控制通过），但 AutoCAD 纯 GUI 鼠标键盘绘图不稳定（自绘界面+GPU渲染），不默认用 CUA 绘图
- CAD 控制优先级：COM API > AutoLISP > Script > accoreconsole；CUA 只用于启动/看状态/验证结果
- 已验证：1000×500 矩形+中心线+保存 CAD 文件全链路通过，Hybrid Agent 状态 READY
- Timeout 经验：Agent 600s / Provider 900s；长任务排障依次查 Agent/Provider/Tool/Node timeout
- 详细状态文档: memory/cad-hybrid-agent-state.md
