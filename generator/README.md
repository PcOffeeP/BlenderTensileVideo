# 生成工具

规则见 [DESIGN.md](../DESIGN.md)，状态与成片链接见 [项目 README](../README.md)。本目录提供新的首版程序化场景入口；用户废弃的7秒诊断实现已删除。

| 入口 | 实现版本 | 适用范围与选项 |
|---|---|---|
| [metal_initial.py](metal_initial.py) | `metal-initial-v1.3.0` | `--style ductile` 颈缩分离或 `brittle` 小变形突断；1280×720。 |
| [polymer_initial.py](polymer_initial.py) | `polymer-initial/1.3.0` | `--style dogbone` 大伸长或 `film` 薄膜根部断裂；960×540。 |
| [composite_initial.py](composite_initial.py) | `composite-initial/0.6.0` | `--kind debond` 断裂与脱粘同步或 `brittle` 低位突断；960×540。 |
| [ceramic_initial.py](ceramic_initial.py) | `ceramic-initial/1.2.0` | 陶瓷小形变脆断定性演示，`--out` 指定目录；1280×720。 |
| [ceramic_crack.py](ceramic_crack.py) | `ceramic-partial-crack/0.2.0` | 陶瓷狗骨从两侧向中间开裂、保留中央材料连接的定性候选；默认生成完整场景，验收情况见项目 README。 |
| [unclamped_initial.py](unclamped_initial.py) | `unclamped-flexible-strip/0.1.0` | 柔性高分子试样上端滑出夹口、下端保持夹持的完整场景；提供无滑移对照供检查。 |
| [explosive_fracture.py](explosive_fracture.py) | `composite-explosive-candidate/0.1.0` | 完整场景的复材定性碎裂候选，保留不规则夹持残段及独立碎片；具体样片待用户审核。 |
| [polymer_brittle.py](polymer_brittle.py) | `polymer-brittle/1.2.0` | 0032参考的窄平条小变形脆断；`--out`、`--keys-only`；960×540。 |
| [polymer_mixed.py](polymer_mixed.py) | `polymer-mixed/1.2.0` | 0014参考的逐渐拉长后快速斜裂；当前固定样片按用户可见过程判据确认为半脆半韧，弹塑份额仍未知；`--out`、`--render`、`--checks-only`；1280×720。 |
| [composite_fragmentation.py](composite_fragmentation.py) | `composite-fragmentation/0.2.0` | 旧 full_span 候选被用户否定，停止续跑且不是有效爆炸性模板；`--variant full_span`（默认）沿自由段细束展开，`--variant local`保留0.1局部几何预设；`--out`、`--render`、`--resume`；960×540。 |
| [metal_flat.py](metal_flat.py) | `metal-flat/1.2.0` | 0058参考的平板狗骨有限变形断裂；`--reference`显式来源记录、`--out`、`--render`；960×540。局部缩窄和完整断裂为作者扩展，主模式未知。 |

各入口均为20秒、30fps的定性几何动画，在配置输出中记录实现版本与适用范围，不读取 `_work/` 输入。除开裂、未夹紧与爆炸性补充入口外，其余入口的参数支持第一阶段及[首批新增设计](../docs/training-batch1-design.md)中的有限候选；新增允许值仍需资格、组合和逐片验收，未标定本构，未批准连续范围。当前金属代码是1.3.0；本轮颈缩成片仍记录原1.0.1配置，以其同名JSON及自包含烘焙场景精确追溯，不因代码复制而改写成片版本。

在项目根目录运行，输出使用新的绝对目录，避免覆盖待验收候选：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/metal_initial.py -- --style brittle --out /absolute/new/output/metal --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_initial.py -- --style dogbone --out /absolute/new/output/polymer
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/composite_initial.py -- --kind debond --out /absolute/new/output/composite --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/ceramic_initial.py -- --out /absolute/new/output/ceramic --render
```

局部开裂入口默认生成包含试样与装置的完整视角；入口检查相机中的裂缝、装置和夹爪投影范围，并逐帧检查两侧裂口、中央材料桥、材料连通及夹口。图像可辨性、材料依据、用户验收和连续参数范围仍须分别判断。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 2 --python-exit-code 1 --python generator/ceramic_crack.py -- --out /absolute/new/output/crack --render
```

编码开裂入口时采用复材及陶瓷的 `frames/frame_%04d.png` 命名。后续 ROI 从完整视频另行裁剪；局部关键帧或特写仅供按需检查，不是第二条测评候选。需要渲染完整特写视频时必须显式加 `--inspection-only`。源视频、时间映射、预期与人工真值和检查限制仍须写入配套 JSON。

未夹紧入口生成包含两端夹具和试样的完整场景，输出 `frames/frame_%04d.png`。`--control-no-slip` 可用于相同几何与夹具行程的内部对照，不是另一个测评候选。滑移、卸载和回弯为定性运动学构造；真实夹持力、摩擦及材料参数未知。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 2 --python-exit-code 1 --python generator/unclamped_initial.py -- --out /absolute/new/output/unclamped --render
```

爆炸性入口生成完整机架、夹具及试样画面，输出 `frames/frame_%04d.png`。夹持残端与不同大小的自由材料段来自可追溯的定性网格分区；碎片数量、形状与运动为作者设定，不复现论文加载速率，不构成材料本构或物理动力学求解。须分别完成编码、来源与标签记录、适用几何检查和用户审核。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 2 --python-exit-code 1 --python generator/explosive_fracture.py -- --out /absolute/new/output/explosive --render
```

金属、复材和陶瓷省略 `--render` 时只制作场景、关键预览和网格检查；高分子加 `--keys-only` 跳过600帧全渲染。Blender入口输出PNG、场景与检查配置；最终MP4编码及来源/标签JSON打包另行完成，不能把裸渲染当作完整交付。PNG序列分别为金属 `frames/%04d.png`、高分子 `frames/%06d.png`、复材及陶瓷 `frames/frame_%04d.png`。例如金属编码：

```sh
ffmpeg -framerate 30 -start_number 1 -i /absolute/new/output/metal/frames/%04d.png -frames:v 600 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart /absolute/new/output/metal/candidate.mp4
```

已在Blender 5.2.1 LTS制作本轮候选并检查实际求值网格和编码。复制到本目录的代码与工作实现字节相同，不为复制操作重复渲染。再生成仍须检查成片、完善来源与六组标签JSON、独立复核，并交用户验收；接受后才收录到 `outputs/current/`。场景、候选、抽帧与日志保留在工作目录。

颈缩参数 `--neck-local-stretch-amplitude` 仅适用于金属 `ductile`，默认4.0。它是局部轴向伸长增量，长度由材料坐标积分，半径按局部伸长的平方根倒数耦合变化。工程守卫为有限 `0 < A ≤ 4.0`，不是批准的材料/视觉连续范围；在 `brittle` 上显式传该参数会被拒绝。更弱离散值2.0的早期检查限于网格／关键状态；第一阶段新成片的当前核验与待验收状态见README和index，接受的基准视频保持不变。

高分子1.1.1补机械连接、全机取景及顶梁净间隙，试样600帧顶点坐标/拓扑与1.0对比；复材沿用已去后板与孤立机架柱的夹具和试样视图；debond0.4.0样片按用户进一步纠正将断裂与局部界面脱粘放在同一事件；brittle分支保留0.3.1配置，已接受旧成片不改写。陶瓷身份来自用户确认的video_0050，完整脆断是超出其可见裂纹阶段的初版建模扩展，原标签表与用户确认分别保存。

本轮补充三个固定基准入口，配置随生成输出并写入同名成片JSON。它们是用于逐条验收的候选模板：脆性窄平条不沿用大伸长动画，有限变形斜裂不把原标签直接作为混合机制核验，复材快速分束不使用事前附件线或闪光作为碎裂。固定基准数值不是可任意组合的已批准范围。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_brittle.py -- --out /absolute/new/output/polymer_brittle
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/polymer_mixed.py -- --out /absolute/new/output/polymer_mixed --render
/Applications/Blender.app/Contents/MacOS/Blender --background --python generator/composite_fragmentation.py -- --out /absolute/new/output/composite_fragmentation --render
```

新增PNG序列：脆性高分子 `frames/%06d.png`；有限变形高分子与复材分束 `frames/frame_%04d.png`。省略全渲染时仍输出关键状态和配置；`polymer_mixed.py --checks-only` 单独检查600帧。最终编码及来源标签包装仍须完成，裸入口输出不等于可收录或可训练视频。

平板入口使用矩形截面和原生共享材料边界缓存。未裂区删除重合内部断面，渐进开裂阶段保留有限面积连接，最后连接切断后保持静止；保存场景通过自身网格与显隐关键帧播放，不读取外部处理脚本。1.1.0以重合坐标检查连接的草稿已拒绝，不是可用基准。

`--reference`是独立的显式JSON输入，包含`source_id`、`source_path`、`source_sha256`、`structure`（`flat_strip`或`flat_dogbone`）、`source_labels`、`observations`、`unknowns`、`source_time_mapping`和`geometry_assumptions`。入口核对源文件SHA；来源内容由制作与复核人员核实，字段齐全不证明材料行为。当前固定局部伸长增量0.18、均匀伸长增量0.02，宽厚收缩指数0.58/0.42仅为作者耦合假设，不能推广为源实验测量或批准范围。输出`frames/%06d.png`、配置、关键状态、实际网格检查及待完善的成片JSON；仍须最终编码、独立复核与用户验收。

旧分束入口0.2.0区分两个固定预设：`full_span`扩大沿自由段的纵向分束范围，采用42个不等宽/深度分区的几何束、连续弯曲及参差裂端；分区数与三维轨迹为作者定性配置，不代表源铺层或真实单丝数量。`local`保留六束中部展开的0.1离散几何，旧成片仍以原JSON实现版本追溯。新版配置明确`variant`与`geometry_preset_version`；参数范围仍须分别核验。用户0040与反馈为主要依据，岛津V18连续帧仅补纵向分裂形态，不移用材料身份、尺寸、时间或幅度。

用户已否定0.2/full_span的爆炸性视觉效果，并要求搁置这一款。代码保留为过程追溯，不继续生成，也不作为已核验爆炸性模板。旧local视频此前接受记录保持；2026-11-15用户已授权制作新的独立样片，旧0.2方案仍不续跑。

## 第一阶段断裂参数入口

用途与离散候选见 [专项设计](../docs/fracture-variation-stage1.md)；候选视频、核验结果及待办仍只在 [项目入口](../README.md) 和 [总索引](../outputs/index.json) 维护。新版本默认值用于与旧固定基准回归，已接受成片的同名JSON仍记录其原版本。工程守卫不表示材料、视觉或连续范围通过。

| 入口 | 断裂相关参数 | 适用边界 |
|---|---|---|
| 金属 | `--neck-local-stretch-amplitude`、`--neck-material-sigma`、`--fracture-material-center`、`--fracture-complete-time-s` | 前两项仅韧断；位置守卫整个裂区及适用颈缩区；省略时间保留各样式原事件。 |
| 高分子大伸长 | `--stretch-increment-factor`、`--fracture-material-fraction`、`--event-time-s` | 新参数仅dogbone；film保持固定基准。装置随行程耦合，构图失败会阻断成片制作，1.15倍在当前相机下未通过。 |
| 高分子窄平条脆断 | `--fracture-material-fraction`、`--event-time-s` | 保持小伸长、原裂面和断后停止；全裂区在模拟标距内。 |
| 高分子半脆半韧 | `--stretch-increment-factor`、`--fracture-center-material-z`、`--event-time-s` | 伸长与既有裂纹阶段加载增量耦合；保持无明显颈缩和最终快速脆断。 |
| 复材 | `--fracture-center`、`--event-time-s`、`--debond-length-factor`、`--debond-opening-factor` | 后两项仅debond；脱粘与断裂同起始事件；brittle位置仍标距外非根部。 |
| 陶瓷 | `--fracture-center-z`、`--final-disconnection-time-s` | 完整裂区在模拟标距内；保留原裂纹发展阶段和断后静止。 |

第一阶段离散时间候选为12、15、17秒；首批新增允许值按下表分别扩展，按实际最终失去贯通连接事件核验。各入口的省略默认值保持原基准。配置、起裂锚点、首次实际开口及失去连接的时间分别保存。完整动画以各入口为准；金属保存烘焙动画，其余入口的静态场景不能单靠`frame_set`重放整片。

运行Blender Python入口时，在`--`之前使用`--python-exit-code 1`，并核对成功日志、600张帧及最终编码；仅进程退出码或旧帧缓存不足以证明制作成功。例如：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 2 --python-exit-code 1 --python generator/metal_initial.py -- --style ductile --neck-local-stretch-amplitude 2 --out /absolute/new/output/metal-a2 --render
```

## 首批新增离散参数支持

按[首批新增设计](../docs/training-batch1-design.md)扩展解析和配置输出；入口支持不表示新增值已通过材料、画面或组合检查，实际结果见README/index。

| 入口 | 本批新增允许值 | 适用边界 |
|---|---|---|
| 金属 | 最终失贯通14、16秒 | 原韧断／脆断分支；A与位置沿用原工程守卫 |
| 高分子大伸长 | 倍率0.90、0.925、0.95、0.975；16.5秒 | 仅dogbone，film固定；1.15诊断支持不表示构图通过 |
| 高分子窄平条 | 14秒 | 原小伸长、位置及裂面 |
| 高分子半脆半韧 | 倍率1.05、1.075、1.10；15.5秒 | 原视觉判据与阶段映射 |
| 复材 | 长度0.9、开口1.1；16秒 | 长度／开口仅debond；brittle中心−1.89沿用原位置守卫 |
| 陶瓷 | 13秒 | 原裂纹发展窗口及断后静止 |

新配置记录实现版本、允许值与适用范围。新增时间沿用各模板原阶段映射；旧成片版本与接受记录不反写。资格及有限回归、600帧实际求值、最终编码、独立复核和逐片接受分别记录。

## 独立合成脆断与韧断样片

[independent_fracture.py](independent_fracture.py)（`independent-fracture/0.1.0`）独立构造陶瓷样条脆断与金属平板韧断两种固定配置，不读取任何视频或旧场景。它是几何动画而非材料本构求解器。原韧断采用逐侧开裂，已被用户否定；保留代码与旧候选供追溯，不用于本次修正批次。配置固定为1280×960、30fps，输出编号从0开始；脆断在第360帧失贯通，旧韧断在第315帧开始几何开裂、第390帧失贯通。静止状态与事件帧的具体实现、假设和检查范围见候选配套 JSON；这两个离散配置的候选不代表连续参数范围或材料行为已接受。

在 Blender 5.2.1 LTS 和 FFmpeg 环境中，指定新的输出目录运行，入口不依赖工作区：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 4 --python-exit-code 1 --python generator/independent_fracture.py -- --kind brittle --mode render --out /absolute/output/brittle-frames
/Applications/Blender.app/Contents/MacOS/Blender --background -t 4 --python-exit-code 1 --python generator/independent_fracture.py -- --kind ductile --mode render --frame-start 0 --frame-end 390 --out /absolute/output/ductile-frames
python3 generator/independent_fracture_encode.py --kind brittle --frames /absolute/output/brittle-frames --output /absolute/output/brittle.mp4
python3 generator/independent_fracture_encode.py --kind ductile --frames /absolute/output/ductile-frames --output /absolute/output/ductile.mp4
```

脆断只渲染两个静态状态；韧断渲染0–390帧，编码器以最终静止画面补足391–599帧。编码器使用 H.264 的无损编码模式保存转换后的 YUV420 画面，避免静止画面因时间压缩产生逐帧波动；RGB 到 YUV420 有色度抽样。旧输出不会被编码器覆盖。`--mode preview` 渲染关键状态；`--mode audit` 对实际求值网格逐帧记录组件、截面、裂面对应点、夹口面和传力部件包围盒。另可用 [independent_fracture_gauge_audit.py](independent_fracture_gauge_audit.py) 的 `--kind` 和 `--out` 参数测量同一作者定义材料段的长度、截面及闭合截取体积。包围盒与对应点检查不能代替全部几何穿透、科学合理性或人工验收。

## 独立合成批次：整截面突断

[independent_batch.py](independent_batch.py)（`independent-fracture-batch/0.1.0`）读取 [independent_batch_configs.json](independent_batch_configs.json) 中八个离散配置，不读取真实实验视频、旧视频或旧场景。变化机架、夹具、试样颜色及外形、断裂材料位置和时间。试样截面为矩形；韧断在变形颈缩之后整截面同一帧断开，不含逐侧撕裂。各参数是作者设定的定性几何近似，不是材料本构标定或已批准的连续范围。首帧已断、仅一帧断前、末帧断裂的可判定边界见对应 JSON。

使用 Blender 5.2.1 LTS 和 FFmpeg，选择新的输出目录与视频路径：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background -t 4 --python-exit-code 1 --python generator/independent_batch.py -- --case ductile_02 --mode render --out /absolute/new/output/ductile_02_frames
python3 generator/independent_batch_encode.py --case ductile_02 --frames /absolute/new/output/ductile_02_frames --output /absolute/new/output/ductile_02.mp4
/Applications/Blender.app/Contents/MacOS/Blender --background -t 4 --python-exit-code 1 --python generator/independent_batch.py -- --case ductile_02 --mode audit --out /absolute/new/output/ductile_02_audit
```

渲染只计算不同动画状态，重复的静止状态通过同内容帧填充为600帧；编码器不覆盖已有成片，并采用 H.264 的 YUV420 域无损编码，RGB 转换时仍有色度抽样。`preview` 可生成关键状态，`audit` 逐帧检查实际求值网格连通性、对应断面间隙、夹口面与传力部件包围盒、同一材料段、断后状态及非相邻三角面相交；相同网格重复使用相交检查结果。后者排除共享顶点的面，包围盒不证明接触力或全部部件无穿透。新生成视频还须单独整理来源、预期与核验标签及配套 JSON，并完成适用检查和人工验收。

## 统一视频标注导出

[export_video_labels.py](export_video_labels.py)（`unified-video-label-export/1.1`）从总索引读取已接受或检查通过待接受的视频，核对媒体、标签与文件校验值，输出一个集中 Excel 工作簿和同内容 CSV。主表沿用真实实验标签五列；核验说明保存完整六组标签、状态、媒体路径和已记录工程事件，主表时间采用实际模拟最终失去贯通连接的事件，说明页记录精确秒、帧及原测量字段；精确首次视觉分离未知继续单独保存。需要 Python、openpyxl 和 ffprobe，不读取固定 `_work/` 输入，不更改视频、元数据或接受状态。

```sh
python3 generator/export_video_labels.py --index outputs/index.json --output-dir /absolute/new/label-output
```

适用范围为整段模拟视频标注整理；不创建下游13列输入或训练发布，不向切片复制整片标签。
