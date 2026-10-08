# 生成工具

规则见 [DESIGN.md](../DESIGN.md)，状态与成片链接见 [项目 README](../README.md)。本目录提供新的首版程序化场景入口；用户废弃的7秒诊断实现已删除。

| 入口 | 实现版本 | 适用范围与选项 |
|---|---|---|
| [metal_initial.py](metal_initial.py) | `metal-initial-v1.0.2` | `--style ductile` 颈缩分离或 `brittle` 小变形突断；1280×720。 |
| [polymer_initial.py](polymer_initial.py) | `polymer-initial/1.0` | `--style dogbone` 大伸长或 `film` 薄膜根部断裂；960×540。 |
| [composite_initial.py](composite_initial.py) | `composite-initial/0.2.0` | `--kind debond` 局部脱粘或 `brittle` 低位突断；960×540。 |

三者均为20秒、30fps的定性几何动画，在配置输出中记录实现版本与适用范围，不读取 `_work/` 输入。参数只对应离散首版候选，未标定本构，未批准连续范围。当前金属代码是1.0.2；本轮颈缩成片仍记录原1.0.1配置，以其同名JSON及自包含烘焙场景精确追溯，不因代码复制而改写成片版本。

在项目根目录运行，输出使用新的绝对目录，避免覆盖待验收候选：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/metal_initial.py -- --style brittle --out /absolute/new/output/metal --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_initial.py -- --style dogbone --out /absolute/new/output/polymer
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/composite_initial.py -- --kind debond --out /absolute/new/output/composite --render
```

金属和复材省略 `--render` 时只制作场景、关键预览和网格检查；高分子加 `--keys-only` 跳过600帧全渲染。Blender入口输出PNG、场景与检查配置；最终MP4编码及来源/标签JSON打包另行完成，不能把裸渲染当作完整交付。PNG序列分别为金属 `frames/%04d.png`、高分子 `frames/%06d.png`、复材 `frames/frame_%04d.png`。例如金属编码：

```sh
ffmpeg -framerate 30 -start_number 1 -i /absolute/new/output/metal/frames/%04d.png -frames:v 600 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart /absolute/new/output/metal/candidate.mp4
```

已在Blender 5.2.1 LTS制作本轮候选并检查实际求值网格和编码。复制到本目录的代码与工作实现字节相同，不为复制操作重复渲染。再生成仍须检查成片、完善来源与六组标签JSON、独立复核，并交用户验收；接受后才收录到 `outputs/current/`。场景、候选、抽帧与日志保留在工作目录。
