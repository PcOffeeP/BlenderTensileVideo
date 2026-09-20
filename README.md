<!-- DOCUMENT-CONTRACT
Purpose: 提供 Blender 拉伸原型的文档、运行、联合审查与验证入口。
Scope: 仓库导航、已验收单视频复现、断裂大类审查批次、交付文件与检查边界。
Must Preserve:
- 以 docs/phase-1-task.md 为整体生成工作的上位依据，docs/MVP.md 记录当前阶段的落实与总结。
- 数据交付为完整 MP4 及同名视频级 JSON；下游接入状态不得冒称通过。
- 后续合成微调试点的配额和门禁指向独立设计文档，不能把候选参考或目标配额写成已完成产物。
- 新类别的试验视频在完成门禁前留在 artifacts/；通过画面、媒体和独立复核后才复制到正式 outputs/；Blender 自动运行要返回可靠错误码。
Non-goals:
- 未经逐类审查直接生成 88 条试点数据，或替代现有数据处理链路。
-->

# BlenderTensileVideo

使用 Blender 生成一条金属扁平哑铃形试样的拉伸、颈缩及韧性断裂视频，断裂位于标距内部。固定输出为 10 秒、30 FPS、854×480，7.0 秒首次完全断离。

## 文档

- [整体生成任务书](docs/phase-1-task.md)：保留原文，作为后续生成工作的目标、标签语义与交付边界依据。
- [MVP 约束与过程总结](docs/MVP.md)：目标、冻结场景、v0.2 动画与标签、生成验收及当前状态。
- [首条 QA 报告](docs/qa-synthetic_0001.md)：视频及标签检查结果、独立复核与接入限制。
- [合成微调可行性试点设计](docs/synthetic-pilot-design.md)：88 条目标配额、原型参考门禁、双源数据入口与基座对照试验。
- [第二条 QA 报告](docs/qa-synthetic_0002.md)：金属脆性断裂视频的断口、编码、标签、连续性与复现证据。
- [断裂大类联合审查批次 QA](docs/qa-major-fracture-review-batch.md)：六条新增候选的覆盖、媒体检查、审查重点与发布边界。

v0.2 已将最终断离改为短促的局部卸载：7.0 秒首次完全断离，自由断口在随后三帧有限回缩，夹持端保持锚定，之后不反弹。

首条 [完整视频](outputs/synthetic_0001.mp4) 和 [视频级标签](outputs/synthetic_0001.json) 已生成，单视频质量检查通过。下游直接读取同名 JSON 的接入验收尚未完成；完成本条后停止，未进行批量生成。

## 单条复现

需要 Blender、Python 3、ffmpeg/ffprobe；像素连续性检查另需 NumPy。以下命令从仓库根目录执行，Blender 可执行路径按安装位置调整。配置固定为 `configs/synthetic_0001.json`，本实现不提供批量入口。

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_golden_prototype.py -- --stage scene
```

查看 `artifacts/previews/scene_gate_initial.png`，完成 Scene Gate 后再生成动画关键状态：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_golden_prototype.py -- --stage keyframes
```

检查 `artifacts/previews/` 的初始、颈缩、断前相邻帧、首次完全断离、三帧卸载过程和稳定断后状态，再正式渲染：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_golden_prototype.py -- --stage final
```

渲染成功后，用同一配置写标签并检查媒体。`--contract` 显式指向现有数据项目的权威标签契约，以下以相邻 `mVllm_2` 仓库为例：

```bash
python3 scripts/write_labels.py --config configs/synthetic_0001.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json
python3 scripts/validate_output.py --config configs/synthetic_0001.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json
python3 scripts/check_continuity.py outputs/synthetic_0001.mp4
```

正式数据文件位于 `outputs/synthetic_0001.mp4` 与 `outputs/synthetic_0001.json`；预览、场景与机器检查证据位于 Git 忽略的 `artifacts/`。重复执行会重建这些本地生成产物。`--stage final` 不替代前两步人工画面检查。

视频标签只复用 v4.1 的机制、位置与特殊情况枚举；帧窗口标签、子视频、采样帧和训练 release 继续属于现有数据链路。当前发现该链路源入口读取 CSV，直接读取本项目同名 JSON 的支持仍需单独确认。

## 金属脆性断裂视频

`configs/synthetic_0002.json` 为首个新机制视频：保持现有金属试样、夹具、正面机位及中性光照，在第 181 帧（6.0 秒）首次完全断离。断口采用轻微斜向、非周期性的互补不规则轮廓；上夹具在断离时停止，断口只作短暂局部卸载，随后间隙稳定。先检查关键帧，再渲染完整视频：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_metal_brittle_gate.py
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_metal_brittle_video.py -- --stage keyframes
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_metal_brittle_video.py -- --stage video
```

`--python-exit-code 1` 让配置不合法或脚本报错时返回非零退出码，自动构建必须保留此选项。渲染和门禁证据先保存在 Git 忽略的 `artifacts/prototypes/metal_brittle/`；渲染完成后执行：

```bash
python3 scripts/write_labels.py --config configs/synthetic_0002.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json --output-dir artifacts/prototypes/metal_brittle
python3 scripts/validate_output.py --config configs/synthetic_0002.json --contract ../mVllm_2/pipeline/contracts/tensile_vlm_v4_1.json --output-dir artifacts/prototypes/metal_brittle --render-evidence artifacts/prototypes/metal_brittle/render-evidence.json --report artifacts/prototypes/metal_brittle/media-qa.json
python3 scripts/check_continuity.py artifacts/prototypes/metal_brittle/synthetic_0002.mp4 --config configs/synthetic_0002.json --report artifacts/prototypes/metal_brittle/continuity-qa.json
```

`render-evidence.json` 只用于内部 QA，绑定本次构建的配置、脚本和 MP4 哈希，不属于 Blender 对下游的同名文件交付，也不定义子视频切片。

画面、媒体和独立复核通过后，正式交付为 `outputs/synthetic_0002.mp4` 与 `outputs/synthetic_0002.json`。它们与候选目录中的已验收文件逐字节一致；本条是已完成的单视频原型，尚未计入后续 70/18 批量数据划分。

## 断裂大类联合审查批次

`configs/synthetic_0003.json` 至 `synthetic_0008.json` 组成一次性视觉审查批次，与已验收的 `0001/0002` 一并覆盖 V4.1 的五种断裂机制和三种断裂位置。它不是 88 条试点批量数据，也不执行机制与位置的笛卡尔积：

| ID | 材料 | 机制 | 位置 |
| --- | --- | --- | --- |
| `0003` | 高分子 | 韧性断裂 | `inside_gauge` |
| `0004` | 复材 | 界面脱粘 | `inside_gauge` |
| `0005` | 复材 | 爆炸性断裂 | `inside_gauge` |
| `0006` | 金属 | 半脆半韧断裂 | `inside_gauge` |
| `0007` | 金属 | 韧性断裂 | `outside_gauge_non_root` |
| `0008` | 金属 | 脆性断裂 | `grip_root` |

统一生成器先为每条渲染五张关键状态图，画面门禁全部通过后才渲染完整视频：

```bash
for id in 0003 0004 0005 0006 0007 0008; do
  /Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_major_fracture_review_batch.py -- --id "$id" --stage keyframes
done

for id in 0003 0004 0005 0006 0007 0008; do
  /Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python scripts/build_major_fracture_review_batch.py -- --id "$id" --stage video
done
```

完整视频生成后，逐条用 `scripts/write_labels.py` 写入简洁同名 JSON，再运行 `scripts/validate_major_fracture_review_batch.py` 汇总媒体、标签、关键帧和构建来源检查。候选保存在 Git 忽略的 `artifacts/review_batches/major_fractures_v1/`；用户完成联合视觉审查前不复制到 `outputs/`。`scripts/build_major_fracture_review_batch_v06.py` 只用于保存早期候选的精确来源，新的重建使用当前生成器。`0006` 因缺少可靠真实近景参考，始终作为待用户判断的视觉语义候选，不因技术检查通过而自动取得批量生成资格。

<!-- DECISION-LOG
D001 — 曾将规则入口集中指向 docs/MVP.md（已由 D002 替代），运行命令继续保留在 README。
Why: 按用户要求整合多轮设计，避免 README 与旧任务书、场景规格、补充文档形成平行入口。
D002 — 分别链接整体生成任务书、当前 MVP 总结与单条 QA。
Supersedes: D001
Why: 用户要求整体任务书继续独立保留并指导后续工作，MVP 总结不取代其地位。
D003 — 另设后续合成微调试点设计入口，不改写首条 MVP 的运行与验收历史。
Why: 88 条可行性试点包含新的标签覆盖、数据接入和真实对照门禁，不能混作首条 Golden Prototype 的已验收范围。
D004 — 新类别先以 Git 忽略的单条候选视频验证视觉、标签与媒体；构建命令显式设置 Blender Python 失败退出码。
Why: 先做可重建原型门禁，并防止自动化在配置不合法而 Blender 默认仍返回零退出码时误用旧视频。
D005 — 新类别候选通过画面、媒体和独立复核后，才将同名 MP4/JSON 复制到 outputs 作为正式单视频交付。
Why: artifacts 用于可重建证据和试验候选；用户需要从 outputs 直接找到最终数据文件，候选与正式交付不能混淆。
D006 — 将六条新类别候选与已验收的 0001/0002 组成一次联合审查，候选在审查通过前保留于 artifacts。
Why: 用户要求先一次性查看整体断裂大类，再决定哪些原型可进入 88 条试点生成；联合审查不等于正式发布或规模化授权。
-->
