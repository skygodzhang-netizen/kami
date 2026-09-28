# 项目合并与标准化工作流 / Project Consolidation Workflow

**版本**: v1.5.0  
**适用场景**: 多版本文件并存、目录结构混乱的项目整合

---

## 快速开始

```bash
# 扫描项目现状
python scripts/consolidate_project.py --scan /path/to/project

# 生成合并方案
python scripts/consolidate_project.py --plan /path/to/project

# 执行合并（需用户确认）
python scripts/consolidate_project.py --execute /path/to/project
```

---

## 合并前检查清单

### 1. 文件版本识别

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 列出所有文件 | `find . -type f -name "*.md" -o -name "*.json"` | 识别所有待合并文件 |
| 识别多版本 | `ls -la *.{md,json} | grep -E "v[0-9]"` | 标记带版本号的文件 |
| 检查修改时间 | `ls -lt` | 按时间排序确定最新版本 |

### 2. 目录结构评估

| 现状 | 评估标准 | 处理建议 |
|------|---------|---------|
| 文件分散根目录 | >10个文件在根目录 | 需要标准化目录结构 |
| 版本文件混乱 | 存在v1/v2/v3并存 | 需要版本合并 |
| 缺少标准目录 | 无config/memory/outline | 需要创建标准目录 |
| 命名不规范 | 文件名格式不统一 | 需要重命名 |

### 3. 配置文件检查

| 必需文件 | 检查命令 | 缺失处理 |
|---------|---------|---------|
| novel_writer_config.json | `test -f config/novel_writer_config.json` | 从最新版本复制或创建默认 |
| workflow_state.json | `test -f workflow/workflow_state.json` | 从最新版本复制或创建默认 |
| character_cards.json | `test -f memory/character_cards.json` | 从最新版本复制或合并 |
| voice_config.json | `test -f config/voice_config.json` | 从最新版本复制 |

---

## 合并决策流程

```
扫描项目
    ↓
识别多版本文件
    ↓
对每个文件组：
    ├─ 配置文件 → 取最新版本
    ├─ 角色卡 → 按时间线合并
    ├─ 大纲 → 取最新版本
    ├─ 章节 → 保留所有，按编号整理
    └─ 草稿 → 保留最新
    ↓
生成合并方案
    ↓
用户确认
    ↓
执行合并
    ↓
验证完整性
```

---

## 合并策略详解

### 策略1: 取最新版本

**适用文件**: 配置文件、大纲文件、声音配置

**决策标准**:
- 修改时间最新
- 版本号最高
- 内容最完整

**操作步骤**:
1. 列出所有版本文件
2. 按修改时间排序
3. 取最新版本复制到标准位置
4. 旧版本归档到archive/

### 策略2: 按时间线合并

**适用文件**: 角色卡、workflow_state

**决策标准**:
- 保留所有历史记录
- 按时间顺序整合
- 解决冲突（取最新）

**操作步骤**:
1. 读取所有版本
2. 提取history数组
3. 按chapter/timestamp排序
4. 合并到单一文件
5. 去重（相同chapter保留最新）

### 策略3: 保留所有

**适用文件**: 章节终稿

**决策标准**:
- 每章终稿都保留
- 按章节号重命名
- 移动到标准目录

**操作步骤**:
1. 识别所有章节文件
2. 提取章节号
3. 统一命名为chapter-XXX-final.md
4. 移动到chapters/final/

### 策略4: 保留最新

**适用文件**: 草稿文件

**决策标准**:
- 只保留最新草稿
- 旧草稿可删除

**操作步骤**:
1. 列出所有草稿文件
2. 按修改时间排序
3. 保留最新版本
4. 删除旧版本（或归档）

---

## 标准化目录创建

### 目录结构模板

```bash
#!/bin/bash
# create_standard_structure.sh

PROJECT_ROOT="$1"

cd "$PROJECT_ROOT" || exit 1

# 创建标准目录
mkdir -p config
mkdir -p memory/worldbuilding
mkdir -p memory/relationships
mkdir -p outline/volume_1
mkdir -p outline/volume_2
mkdir -p chapters/outline
mkdir -p chapters/draft
mkdir -p chapters/final
mkdir -p workflow
mkdir -p archive/v1.0
mkdir -p archive/v2.0
mkdir -p scripts

echo "标准目录结构创建完成"
```

### 必需文件模板

**novel_writer_config.json**:
```json
{
  "book_title": "未命名小说",
  "genre": "玄幻",
  "sub_genre": "洪荒",
  "target_words": 1000000,
  "current_chapter": 1,
  "current_volume": 1,
  "chapters_per_volume": 50,
  "total_volumes": 3,
  "protagonist": {
    "name": "主角",
    "personality": "钢铁直男",
    "current_power": "太乙金仙"
  },
  "checkpoint_items": [],
  "created_at": "2026-01-01T00:00:00+08:00",
  "updated_at": "2026-01-01T00:00:00+08:00"
}
```

**workflow_state.json**:
```json
{
  "current_chapter": 1,
  "current_stage": "outline",
  "workflow_progress": {},
  "pending_tasks": [],
  "character_updates_pending": [],
  "notes": [],
  "updated_at": "2026-01-01T00:00:00+08:00"
}
```

**character_cards.json**:
```json
{
  "characters": {
    "protagonist": {
      "id": "protagonist",
      "name": "主角",
      "created_at": 1,
      "current_status": {
        "power_level": 1,
        "mood": "平静"
      },
      "history": [],
      "relationships": {}
    }
  },
  "factions": {},
  "relationships": {}
}
```

---

## 合并执行脚本

```python
#!/usr/bin/env python3
# consolidate_project.py

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

class ProjectConsolidator:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.scan_results = {}
        self.merge_plan = {}
        
    def scan(self):
        """扫描项目现状"""
        print(f"扫描项目: {self.project_path}")
        
        # 扫描所有文件
        all_files = list(self.project_path.rglob('*'))
        files = [f for f in all_files if f.is_file()]
        
        # 分类统计
        self.scan_results = {
            'total_files': len(files),
            'config_files': [],
            'chapter_files': [],
            'outline_files': [],
            'multi_version_files': [],
            'orphan_files': []
        }
        
        for f in files:
            # 识别多版本文件
            if any(x in f.name for x in ['v1', 'v2', 'v3', 'v4', 'v5']):
                self.scan_results['multi_version_files'].append(f)
            
            # 分类文件
            if f.suffix == '.json':
                self.scan_results['config_files'].append(f)
            elif 'chapter' in f.name:
                self.scan_results['chapter_files'].append(f)
            elif 'outline' in f.name:
                self.scan_results['outline_files'].append(f)
        
        return self.scan_results
    
    def generate_plan(self):
        """生成合并方案"""
        print("生成合并方案...")
        
        self.merge_plan = {
            'create_dirs': [
                'config',
                'memory/worldbuilding',
                'outline',
                'chapters/outline',
                'chapters/draft',
                'chapters/final',
                'workflow',
                'archive'
            ],
            'copy_files': [],
            'merge_files': [],
            'archive_files': []
        }
        
        # 处理配置文件
        config_files = self.scan_results['config_files']
        for config_type in ['novel_writer_config', 'workflow_state', 'character_cards']:
            matching = [f for f in config_files if config_type in f.name]
            if matching:
                # 取最新版本
                latest = max(matching, key=lambda f: f.stat().st_mtime)
                self.merge_plan['copy_files'].append({
                    'src': latest,
                    'dst': f'config/{config_type}.json',
                    'strategy': 'latest'
                })
                # 其他版本归档
                for f in matching:
                    if f != latest:
                        self.merge_plan['archive_files'].append({
                            'src': f,
                            'dst': f'archive/{f.name}'
                        })
        
        # 处理章节文件
        chapter_files = self.scan_results['chapter_files']
        for ch_file in chapter_files:
            # 提取章节号
            import re
            match = re.search(r'chapter[_-]?(\d+)', ch_file.name, re.IGNORECASE)
            if match:
                ch_num = int(match.group(1))
                if 'final' in ch_file.name.lower():
                    self.merge_plan['copy_files'].append({
                        'src': ch_file,
                        'dst': f'chapters/final/chapter-{ch_num:03d}-final.md',
                        'strategy': 'rename'
                    })
                elif 'draft' in ch_file.name.lower():
                    self.merge_plan['copy_files'].append({
                        'src': ch_file,
                        'dst': f'chapters/draft/chapter-{ch_num:03d}-draft.md',
                        'strategy': 'rename'
                    })
        
        return self.merge_plan
    
    def execute(self, dry_run=True):
        """执行合并"""
        if dry_run:
            print("【模拟模式】将执行以下操作:")
        else:
            print("【执行模式】开始合并...")
        
        # 创建目录
        for dir_path in self.merge_plan['create_dirs']:
            full_path = self.project_path / dir_path
            if dry_run:
                print(f"  [创建目录] {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ 创建目录: {dir_path}")
        
        # 复制文件
        for file_op in self.merge_plan['copy_files']:
            src = file_op['src']
            dst = self.project_path / file_op['dst']
            if dry_run:
                print(f"  [复制] {src.name} -> {file_op['dst']} ({file_op['strategy']})")
            else:
                shutil.copy2(src, dst)
                print(f"  ✅ 复制: {src.name} -> {file_op['dst']}")
        
        # 归档文件
        for file_op in self.merge_plan['archive_files']:
            src = file_op['src']
            dst = self.project_path / file_op['dst']
            if dry_run:
                print(f"  [归档] {src.name} -> {file_op['dst']}")
            else:
                shutil.move(str(src), str(dst))
                print(f"  ✅ 归档: {src.name}")
        
        if not dry_run:
            print("\n✅ 合并完成!")
            print(f"请检查: {self.project_path}")

# 主函数
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python consolidate_project.py <command> <project_path>")
        print("命令: scan | plan | execute")
        sys.exit(1)
    
    command = sys.argv[1]
    project_path = sys.argv[2]
    
    consolidator = ProjectConsolidator(project_path)
    
    if command == 'scan':
        results = consolidator.scan()
        print(f"\n扫描结果:")
        print(f"  总文件数: {results['total_files']}")
        print(f"  配置文件: {len(results['config_files'])}")
        print(f"  章节文件: {len(results['chapter_files'])}")
        print(f"  大纲文件: {len(results['outline_files'])}")
        print(f"  多版本文件: {len(results['multi_version_files'])}")
    
    elif command == 'plan':
        consolidator.scan()
        plan = consolidator.generate_plan()
        print(f"\n合并方案:")
        print(f"  创建目录: {len(plan['create_dirs'])} 个")
        print(f"  复制文件: {len(plan['copy_files'])} 个")
        print(f"  合并文件: {len(plan['merge_files'])} 个")
        print(f"  归档文件: {len(plan['archive_files'])} 个")
    
    elif command == 'execute':
        consolidator.scan()
        consolidator.generate_plan()
        consolidator.execute(dry_run=False)
```

---

## 合并后验证

### 验证清单

| 检查项 | 验证方法 | 通过标准 |
|--------|---------|---------|
| 目录结构完整 | `ls -R` | 所有标准目录存在 |
| 配置文件可解析 | `python -c "import json; json.load(open('config/novel_writer_config.json'))"` | 无JSON错误 |
| 章节文件完整 | `ls chapters/final/*.md | wc -l` | 章节数正确 |
| 命名规范 | `find . -name "*v[0-9]*"` | 无版本号文件残留 |
| 无重复文件 | `find . -type f -exec md5sum {} \; | sort | uniq -d` | 无重复内容 |

### 验证脚本

```bash
#!/bin/bash
# verify_consolidation.sh

PROJECT_ROOT="$1"

echo "验证项目合并结果..."

# 检查目录结构
for dir in config memory outline chapters workflow; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "✅ 目录存在: $dir"
    else
        echo "❌ 目录缺失: $dir"
    fi
done

# 检查必需文件
for file in config/novel_writer_config.json config/voice_config.json workflow/workflow_state.json; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "✅ 文件存在: $file"
        # 验证JSON格式
        if python3 -c "import json; json.load(open('$PROJECT_ROOT/$file'))" 2>/dev/null; then
            echo "   ✅ JSON格式正确"
        else
            echo "   ❌ JSON格式错误"
        fi
    else
        echo "❌ 文件缺失: $file"
    fi
done

# 统计章节
echo ""
echo "章节统计:"
ls -1 "$PROJECT_ROOT/chapters/final"/*.md 2>/dev/null | wc -l | xargs echo "  终稿章节数:"
ls -1 "$PROJECT_ROOT/chapters/draft"/*.md 2>/dev/null | wc -l | xargs echo "  草稿章节数:"

echo ""
echo "验证完成"
```

---

## 常见问题

### Q1: 如何处理同名但内容不同的文件？

**A**: 按以下优先级:
1. 检查修改时间，取最新
2. 检查文件大小，取较大（通常内容更完整）
3. 人工对比内容差异
4. 必要时合并内容

### Q2: 发现关键配置信息散落在多个文件？

**A**: 
1. 提取所有相关信息
2. 按配置项整合
3. 冲突时以最新版本为准
4. 在notes中记录合并决策

### Q3: 合并后发现数据丢失？

**A**:
1. 立即停止操作
2. 检查archive目录是否有备份
3. 从备份恢复
4. 重新制定合并方案

### Q4: 如何保留合并历史？

**A**:
1. 在workflow_state.json中添加合并记录
2. 保留archive目录
3. 创建MERGE_LOG.md记录合并决策

---

## 最佳实践

1. **备份优先**: 合并前创建完整备份
2. **分步执行**: 先scan，再plan，最后execute
3. **用户确认**: 重大合并决策需用户确认
4. **验证完整性**: 合并后必须验证
5. **记录决策**: 保留合并日志
