#!/bin/bash

SCRIPT=/home/ubuntu/.openclaw/workspace/scripts


echo "=== Metrics Collection Start ==="


# 1. 系统指标采集
bash $SCRIPT/metrics-collect.sh


# 2. iStoreOS指标采集
bash $SCRIPT/istoreos-metrics.sh


# 3. 保存历史数据
bash $SCRIPT/metrics-history.sh


# 4. AI风险分析
bash $SCRIPT/ai-ops-analyzer.sh


# 5. 趋势分析
bash $SCRIPT/disk-growth-analyzer.sh


# 6. 网络质量巡检
bash $SCRIPT/network-health-check.sh


# 7. 网络质量评分
bash $SCRIPT/network-score-analyzer.sh


bash $SCRIPT/ai-summary-generator.sh


echo "=== Metrics Collection Finished ==="
