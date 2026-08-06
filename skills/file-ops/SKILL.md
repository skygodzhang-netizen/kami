# file-ops — Batch File Operations

## Purpose
批量文件操作：重命名、格式转换、目录同步、按规则整理。

## When to use
- 批量重命名（加前缀、改扩展名、按日期）
- 格式转换（图片压缩、PDF 合并、视频转码）
- 目录同步（本地/远程、增量备份）
- 文件整理（按类型/日期/大小分类到子文件夹）

## Usage

### 批量重命名
```bash
# 加前缀
file-ops rename /photos/*.jpg --prefix "vacation_"

# 按日期重命名
file-ops rename /photos/*.jpg --pattern "{mtime:YYYY-MM-DD}_{index}.jpg"
```

### 格式转换
```bash
# 图片压缩
file-ops convert /photos/*.jpg --to webp --quality 80

# PDF 合并
file-ops merge /reports/*.pdf --output /reports/merged.pdf
```

### 目录同步
```bash
# 本地同步
file-ops sync /source /backup --incremental

# 远程同步
file-ops sync /local user@host:/remote --ssh-key ~/.ssh/id_rsa
```

### 文件整理
```bash
# 按扩展名分类
file-ops organize /downloads --by extension --target /organized

# 按日期分类
file-ops organize /photos --by mtime --pattern "YYYY/MM" --target /photos-archive
```

## Integration points

- **pipeline**: 在流水线中批量处理文件
- **event-watcher**: `event-watcher add auto-convert --path /uploads --command "file-ops convert {{event.path}} --to webp"`

## Notes
- 依赖外部工具（ffmpeg、imagemagick、rsync 等）
- 所有破坏性操作默认需要确认，除非加 `--yes`
- Undo 脚本保存 30 天后自动清理
