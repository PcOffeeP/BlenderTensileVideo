# 可复用拉伸视频生成器

这里保存有明确复用用途的代码与配置。整体规则见 [DESIGN.md](../DESIGN.md)，进度和验收范围统一见 [项目 README](../README.md) 与总索引；本页只说明工具用法。

`render_metal_round.py` 根据配置创建光圆棒、夹具、颈缩和断后两段，输出关键帧、完整 PNG 序列、Blender 场景与基础求值网格检查。它只读取传入配置，不读取旧工作区、历史场景或既有视频。模型使用相对场景单位和受控动画，没有标定的材料定律或力值求解。

## 已使用的运行环境

- Blender 5.2.1 LTS，构建 hash `9e2066aef7ef`。
- FFmpeg 8.1.1，支持 `libx264`。
- Python 标准库及 Blender 内置 `bpy`、`mathutils`。

## 重建当前圆棒基准

在项目根目录执行。示例使用新的工作目录，以保留此前待审版本：

```zsh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --python-exit-code 1 \
  --python generator/render_metal_round.py -- \
  --config generator/configs/metal_round_baseline_v1.json \
  --out _work/rebuild-metal-round
```

只检查构图和关键状态时，在末尾追加 `--preview-only`；这不会输出完整帧序列或完整网格报告。完整渲染后编码：

```zsh
/opt/homebrew/bin/ffmpeg -n \
  -framerate 30 -start_number 1 \
  -i _work/rebuild-metal-round/frames/frame_%04d.png \
  -frames:v 204 -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -movflags +faststart \
  _work/rebuild-metal-round/metal_round_baseline_v1_candidate.mp4
```

本次实际编码采用 libx264 默认 CRF 23；示例将它显式写出。帧率和帧数须与所用配置一致，不能在更换时长后直接沿用本示例数值。不同 Blender/编码器版本下不保证视频字节完全相同。

## 检查与使用边界

基础报告检查实际试样/夹具网格端部连接及断后间隙。其 `component_count` 按当前生成时序写入，不能当作独立的拓扑核验。正式候选仍需重新打开保存场景检查实际可见网格、观察最终编码片，并按整体设计完成适用的独立复核和人工核验；中间检查记录按项目约定保存在工作区，结论提炼到候选/成片 JSON。

当前代码针对随附基准配置建立。夹口位置、几何采样和检查帧等仍有样式内固定假设；配置中声明的可扩展维度不代表所有参数已经实现、任意数值都合法或范围已经确认。新增参数试片时须同步核对相关几何与检查约束。生成入口不会自动分配审核通过标签、收录到 `outputs/` 或发布训练数据。
