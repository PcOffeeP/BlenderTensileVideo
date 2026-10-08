# 生成工具

规则见 [DESIGN.md](../DESIGN.md)，状态与成片链接见 [项目 README](../README.md)。本目录提供新的首版程序化场景入口；用户废弃的7秒诊断实现已删除。

| 入口 | 实现版本 | 适用范围与选项 |
|---|---|---|
| [metal_initial.py](metal_initial.py) | `metal-initial-v1.1.0` | `--style ductile` 颈缩分离或 `brittle` 小变形突断；1280×720。 |
| [polymer_initial.py](polymer_initial.py) | `polymer-initial/1.1.1` | `--style dogbone` 大伸长或 `film` 薄膜根部断裂；960×540。 |
| [composite_initial.py](composite_initial.py) | `debond: composite-initial/0.4.0`；`brittle: composite-initial/0.3.1` | `--kind debond` 断裂与脱粘同步或 `brittle` 低位突断；960×540。 |
| [ceramic_initial.py](ceramic_initial.py) | `ceramic-initial/1.0.1` | 陶瓷小形变脆断定性演示，`--out` 指定目录；1280×720。 |
| [polymer_brittle.py](polymer_brittle.py) | `polymer-brittle/1.0` | 0032参考的窄平条小变形脆断；`--out`、`--keys-only`；960×540。 |
| [polymer_mixed.py](polymer_mixed.py) | `polymer-mixed/1.0.0` | 0014参考的有限变形后快速斜裂候选，混合模式尚未确认；`--out`、`--render`、`--checks-only`；1280×720。 |
| [composite_fragmentation.py](composite_fragmentation.py) | `composite-fragmentation/0.1.0` | 0040参考的局部快速分束候选；`--out`、`--render`、`--resume`；960×540。 |

各入口均为20秒、30fps的定性几何动画，在配置输出中记录实现版本与适用范围，不读取 `_work/` 输入。参数只对应离散首版候选，未标定本构，未批准连续范围。当前金属代码是1.1.0；本轮颈缩成片仍记录原1.0.1配置，以其同名JSON及自包含烘焙场景精确追溯，不因代码复制而改写成片版本。

在项目根目录运行，输出使用新的绝对目录，避免覆盖待验收候选：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/metal_initial.py -- --style brittle --out /absolute/new/output/metal --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_initial.py -- --style dogbone --out /absolute/new/output/polymer
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/composite_initial.py -- --kind debond --out /absolute/new/output/composite --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/ceramic_initial.py -- --out /absolute/new/output/ceramic --render
```

金属、复材和陶瓷省略 `--render` 时只制作场景、关键预览和网格检查；高分子加 `--keys-only` 跳过600帧全渲染。Blender入口输出PNG、场景与检查配置；最终MP4编码及来源/标签JSON打包另行完成，不能把裸渲染当作完整交付。PNG序列分别为金属 `frames/%04d.png`、高分子 `frames/%06d.png`、复材及陶瓷 `frames/frame_%04d.png`。例如金属编码：

```sh
ffmpeg -framerate 30 -start_number 1 -i /absolute/new/output/metal/frames/%04d.png -frames:v 600 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart /absolute/new/output/metal/candidate.mp4
```

已在Blender 5.2.1 LTS制作本轮候选并检查实际求值网格和编码。复制到本目录的代码与工作实现字节相同，不为复制操作重复渲染。再生成仍须检查成片、完善来源与六组标签JSON、独立复核，并交用户验收；接受后才收录到 `outputs/current/`。场景、候选、抽帧与日志保留在工作目录。

颈缩参数 `--neck-local-stretch-amplitude` 仅适用于金属 `ductile`，默认4.0。它是局部轴向伸长增量，长度由材料坐标积分，半径按局部伸长的平方根倒数耦合变化。工程守卫为有限 `0 < A ≤ 4.0`，不是批准的材料/视觉连续范围；在 `brittle` 上显式传该参数会被拒绝。更弱离散值2.0作网格/关键状态验证，无新成片验收，接受的基准视频保持不变。

高分子1.1.1补机械连接、全机取景及顶梁净间隙，试样600帧顶点坐标/拓扑与1.0对比；复材沿用已去后板与孤立机架柱的夹具和试样视图；debond0.4.0样片按用户进一步纠正将断裂与局部界面脱粘放在同一事件；brittle分支保留0.3.1配置，已接受旧成片不改写。陶瓷身份来自用户确认的video_0050，完整脆断是超出其可见裂纹阶段的初版建模扩展，原标签表与用户确认分别保存。

本轮补充三个固定基准入口，配置随生成输出并写入同名成片JSON。它们是用于逐条验收的候选模板：脆性窄平条不沿用大伸长动画，有限变形斜裂不把原标签直接作为混合机制核验，复材快速分束不使用事前附件线或闪光作为碎裂。固定基准数值不是可任意组合的已批准范围。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_brittle.py -- --out /absolute/new/output/polymer_brittle
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_mixed.py -- --out /absolute/new/output/polymer_mixed --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/composite_fragmentation.py -- --out /absolute/new/output/composite_fragmentation --render
```

新增PNG序列：脆性高分子 `frames/%06d.png`；有限变形高分子与复材分束 `frames/frame_%04d.png`。省略全渲染时仍输出关键状态和配置；`polymer_mixed.py --checks-only` 单独检查600帧。最终编码及来源标签包装仍须完成，裸入口输出不等于可收录或可训练视频。
