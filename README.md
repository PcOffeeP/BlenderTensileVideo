<!-- DOCUMENT-CONTRACT
Purpose: 提供首条 Blender 拉伸原型的文档、运行与验证入口。
Scope: 仓库导航、单视频复现命令、交付文件与检查边界。
Must Preserve:
- 以阶段一任务书和 Scene Specification 为上位约束。
- 数据交付为完整 MP4 及同名视频级 JSON；下游接入状态不得冒称通过。
Non-goals:
- 批量生成或替代现有数据处理链路。
-->

# BlenderTensileVideo

使用 Blender 生成一条金属扁平哑铃形试样的拉伸、颈缩及韧性断裂视频，断裂位于标距内部。固定输出为 10 秒、30 FPS、854×480，7.0 秒首次完全断离。

## 文档

- [阶段一任务书](docs/phase-1-task.md)：整体结果与视频级标签要求。
- [Scene Specification v0.1](docs/Scene%20Specification%20v0.1.md)：冻结三维场景模板。
- [设计补充](docs/design-supplement.md)：时间映射、实现细节与下游接入待决项。
- [首条 QA 报告](docs/qa-synthetic_0001.md)：视频及标签检查结果、独立复核与接入限制。

首条 [完整视频](outputs/synthetic_0001.mp4) 和 [视频级标签](outputs/synthetic_0001.json) 已生成，单视频质量检查通过。下游直接读取同名 JSON 的接入验收尚未完成；完成本条后停止，未进行批量生成。

## 单条复现

需要 Blender、Python 3、ffmpeg/ffprobe；像素连续性检查另需 NumPy。以下命令从仓库根目录执行，Blender 可执行路径按安装位置调整。配置固定为 `configs/synthetic_0001.json`，本实现不提供批量入口。

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_golden_prototype.py -- --stage scene
```

查看 `artifacts/previews/scene_gate_initial.png`，完成 Scene Gate 后再生成动画关键状态：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_golden_prototype.py -- --stage keyframes
```

检查 `artifacts/previews/` 的初始、颈缩、断前相邻帧、首次完全断离、断后五张预览，再正式渲染：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_golden_prototype.py -- --stage final
```

渲染成功后，用同一配置写标签并检查媒体。`--contract` 显式指向现有数据项目的权威标签契约，以下以相邻 `mVllm_2` 仓库为例：

```bash
python3 scripts/write_labels.py --config configs/synthetic_0001.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json
python3 scripts/validate_output.py --config configs/synthetic_0001.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json
python3 scripts/check_continuity.py outputs/synthetic_0001.mp4
```

正式数据文件位于 `outputs/synthetic_0001.mp4` 与 `outputs/synthetic_0001.json`；预览、场景与机器检查证据位于 Git 忽略的 `artifacts/`。重复执行会重建这些本地生成产物。`--stage final` 不替代前两步人工画面检查。

视频标签只复用 v4.1 的机制、位置与特殊情况枚举；帧窗口标签、子视频、采样帧和训练 release 继续属于现有数据链路。当前发现该链路源入口读取 CSV，直接读取本项目同名 JSON 的支持仍需单独确认。
