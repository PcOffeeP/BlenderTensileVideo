# Blender 拉伸实验模拟视频

当前方案：[DESIGN.md](DESIGN.md)（v1.11） · 生成工具：[generator/README.md](generator/README.md) · 唯一机器索引：[outputs/index.json](outputs/index.json) · 工作约定：[AGENTS.md](AGENTS.md)。

## 当前状态

2026-10-08，当前 **十一条20秒基础视频已由用户接受并收录**：金属3条、高分子4条、复材3条、陶瓷1条。新金属平板按原候选SHA收录，视频字节保持。高分子半脆半韧已按用户补充的项目视觉判据确认当前样片；新版复材广自由段分束候选已被用户否定，爆炸性断裂生成暂停；旧局部型及其他已接受视频继续保留。样式与连续参数范围、训练发布分别记录，六组生成/验收标签不替代下游训练字段。

用户要求废弃的本轮错误7秒圆棒诊断，其视频、场景、实现与论文调查过程已删除，失效链接与索引已清除。此前收集的原始资料保留。

直接参考 `/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data` 的真实视频及 `video_mapping.csv`、`all_videos_tag.xlsx`，论文不是生成前提。视频目标15–30秒，当前成片均20秒，按来源重定时：较长实验过程压缩，短来源的阶段延长；分别呈现加载、变形、破坏和断后观察；源时间与模拟时间分别记录。

## 当前成果

已接受的十一条原成片按字节校验值收录，原来源、配置及核验范围保持。旧七条JSON的早期 pending 文本保留为历史核验记录，并依据已有独立复核、主Agent观看与用户接受记录追加当前状态澄清，不将定性视觉接受写成机制证明。旧脱粘版本先脱粘后断裂，已被本次用户纠正撤销，不再作为待验收成片。

| 视频 | 来源 | 主要破坏类别 | 模拟位置 | 状态 | 文件（均20秒） |
|---|---|---|---|---|---|
| 金属圆棒颈缩分离 | video_0006 | 韧性断裂 | 标距内 | 已接受 | [视频](outputs/current/metal_round_neck_separation/metal_round_ductile_baseline_v1.mp4) · [JSON](outputs/current/metal_round_neck_separation/metal_round_ductile_baseline_v1.json) |
| 金属圆棒小变形突断 | video_0003 | 脆性断裂 | 标距内 | 已接受 | [视频](outputs/current/metal_round_brittle/metal_round_brittle_baseline_v1.mp4) · [JSON](outputs/current/metal_round_brittle/metal_round_brittle_baseline_v1.json) |
| 高分子大伸长断裂 | video_0097 | 韧性断裂 | 标距内 | 已接受 | [视频](outputs/current/polymer_black_flexible_dogbone/polymer_black_dogbone_baseline_v2.mp4) · [JSON](outputs/current/polymer_black_flexible_dogbone/polymer_black_dogbone_baseline_v2.json) |
| 高分子薄膜夹口根部断裂 | video_0025 | 无法确认 | 夹口根部 | 已接受 | [视频](outputs/current/polymer_yellow_film_root_rupture/polymer_yellow_film_grip_root_baseline_v2.mp4) · [JSON](outputs/current/polymer_yellow_film_root_rupture/polymer_yellow_film_grip_root_baseline_v2.json) |
| 复材近下夹口突断 | video_0100 | 脆性断裂 | 标距外非根部 | 已接受 | [视频](outputs/current/composite_brittle_lower/composite_brittle_lower_feedback_v0_3.mp4) · [JSON](outputs/current/composite_brittle_lower/composite_brittle_lower_feedback_v0_3.json) |
| 陶瓷小形变横向脆断 | video_0050 | 脆性断裂 | 标距内 | 已接受 | [视频](outputs/current/ceramic_dogbone_brittle/ceramic_dogbone_brittle_baseline_v1.mp4) · [JSON](outputs/current/ceramic_dogbone_brittle/ceramic_dogbone_brittle_baseline_v1.json) |
| 复材断裂与界面脱粘同时发生 | video_0020 | 界面脱粘 | 标距内 | 已接受 | [视频](outputs/current/composite_interface_debond_simultaneous_complete/composite_interface_debond_simultaneous_baseline_v0_4.mp4) · [JSON](outputs/current/composite_interface_debond_simultaneous_complete/composite_interface_debond_simultaneous_baseline_v0_4.json) |
| 高分子窄平条脆断 | video_0032 | 脆性断裂（定性视觉） | 标距内 | 已接受 | [视频](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_pale_green_brittle_flat_strip_baseline_v1.mp4) · [JSON](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_pale_green_brittle_flat_strip_baseline_v1.json) |
| 高分子均匀拉长后瞬时脆断 | video_0014 | 半脆半韧（用户确认项目视觉判据） | 标距内 | 已接受 | [视频](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_finite_deformation_oblique_rupture_baseline_v1.mp4) · [JSON](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_finite_deformation_oblique_rupture_baseline_v1.json) |
| 复材快速分束断裂 | video_0040 | 预期爆炸性；核验无法确认 | 标距内 | 已接受 | [视频](outputs/current/composite_rapid_strand_fragmentation/composite_rapid_strand_fragmentation_baseline_v0_1.mp4) · [JSON](outputs/current/composite_rapid_strand_fragmentation/composite_rapid_strand_fragmentation_baseline_v0_1.json) |
| 金属平板有限变形后断裂 | video_0058 | 预期韧性；核验无法确认 | 标距内 | 已接受 | [视频](outputs/current/metal_flat_limited_deformation_rupture/metal_flat_limited_deformation_rupture_baseline_v1.mp4) · [JSON](outputs/current/metal_flat_limited_deformation_rupture/metal_flat_limited_deformation_rupture_baseline_v1.json) |

高分子两条补全夹具、传力杆、移动横梁/导向套、导柱与固定机架的连接，原试样600帧坐标及面拓扑保持；顶梁净间隙已修正。复材两条移除后方大板及孤立机架柱，采用夹具与试样视图；用户纠正脱粘片为断裂时局部界面同时打开，不设置先脱粘后断裂的独立阶段；新版本中二者同在第511帧（17秒）起始，之后停止。位置按照模拟定义的标距归类，来源正式标距未确认。薄膜来源“齐根断裂”只确定位置，机制仍为“无法确认”。

video_0050陶瓷身份由用户确认；原表“其他(无机非)/视频异常”保持。源视频可见逐渐发展的横向裂纹，末态完整分离和具体事件时间缺少直接证据。陶瓷初版的完整脆断为作者定性扩展，材料牌号、微观机制及本构参数未知；不能当成源视频逐帧复现。

金属增加颈缩控制 `--neck-local-stretch-amplitude`，默认4.0保留已接受效果，局部轴向伸长、截面及加载端位置耦合计算。较弱2.0仅生成关键状态并核验；默认值与原场景38帧比对通过浮点容差。工程守卫 `0 < A ≤ 4.0` 不表示连续范围已批准，接受的原成片仍为1.0.1配置。

## 基础模板覆盖与本轮补充

按材料与主要行为补齐适用基准，已有金属脆断直接复用。下表是覆盖与待办入口；“来源待核实”不是已覆盖，也不表示该组合不适用。

| 材料 | 已接受的基础行为 | 本轮补充 | 证据缺口 |
|---|---|---|---|
| 金属 | 圆棒颈缩韧断、小变形脆断、平板有限变形断裂 | 三条固定视频已接受 | 平板主机制仍未知；其他结构与位置组合需分别核验 |
| 高分子 | 大伸长韧断、薄膜根断（机制未知）、窄平条脆断、均匀拉长后瞬时脆断（半脆半韧） | 0032与0014固定视频视觉效果已接受 | 0014按用户确认的可见过程分类为半脆半韧；塑性比例、厚度与具体材料仍未知，具体应变场为作者假设 |
| 复材 | 低位脆断、断裂与界面脱粘同步、快速分束断裂（机制未知） | 0040固定视频视觉效果已接受 | 0040旧局部型主模式仍未知，新广自由段候选被用户否定，爆炸性生成搁置；0030/0099原标签韧性，但延性变形线索不足，暂不计覆盖 |
| 陶瓷 | 小变形脆断定性初版 | 复用现有基准 | 原源完整分离与牌号仍未知；不扩充没有依据的机制 |

三条新增视频均为30fps、600帧。独立实际求值复核确认第481帧（16秒）失去夹口贯通路径；脆断和斜裂断后停止，复材局部运动在第526帧后停止。有限变形视频在476–480帧仍有材料连接，不把可见裂口等同全断；极小未粘结零开口片及检查局限写入JSON。复材加载体积约增加1.68%，属于固定几何近似，不称为不可压缩材料模型。

当前仍有模式与行为缺项。用户已明确半脆半韧的项目判据为断前逐渐、视觉上均匀拉长且无明显颈缩，最终快速脆断；0014现片据此确认，无需证明弹塑份额或修改已接受视频。旧[模式复核](_work/next-baselines-20261008/review/mode_evidence_adjudication.md)保留其当时依据，新[项目视觉判据复核](_work/label-clarification-20261008/review/operational_mode_review.md)支持0014确认，新确认和科学未知分别记录在JSON。0040旧局部成片保留`composite-fragmentation/0.1.0`原视频及接受记录；本轮`0.2.0/full_span`候选已被用户否定，不计爆炸性覆盖。用户认可局部型，未将其废弃；0.2的爆炸性视觉判据核验已撤销；旧局部型不因此升级类别。

金属平板首例参考 video_0058：来源可确认扁平狗骨及夹持，不能确认动态颈缩幅度、精确分离帧或断后轨迹。有限变形、局部缩窄和完整分离分别标记作者定性扩展，主模式保留预期韧性／核验无法确认，不计已核验平板颈缩覆盖。[视频](outputs/current/metal_flat_limited_deformation_rupture/metal_flat_limited_deformation_rupture_baseline_v1.mp4)及[JSON](outputs/current/metal_flat_limited_deformation_rupture/metal_flat_limited_deformation_rupture_baseline_v1.json)已完成20秒、600帧编码与主Agent原生播放器查看，用户接受后按SHA收录。

平板1.1.0草稿被独立检查拒绝：两半只是坐标接触，不构成实际材料连接。1.2.0改为共享索引的原生闭合边界；独立600帧测量确认1–510帧为一个连通体，510帧有有限面积材料连接，511帧切断后为两个连通体，断后试样与装置完全停止。夹口与传力杆/端盖接头误差处于浮点精度范围，最终编码背景裂口可见。渐进裂区体积峰值约+0.674%，最后释放体积下降约0.566%并有局部材料路径变化，属于作者几何近似，不宣称严格体积守恒或最后释放无变形。当前定性候选通过，完整范围见[独立复核](_work/next-baselines-20261008/review/metal_flat_connected_final_review.md)及同名JSON。

已核对七条高分子原韧性来源的初态、中段和事件附近画面，未找到可清楚判读的新生局部颈缩或颈缩传播；保持该样式缺项，不把预制狗骨腰部或整体伸长当作传播。来源筛选范围与未知见[筛选记录](_work/next-baselines-20261008/source-inspection/source_selection.md)。复材韧性0030/0099仍需可辨认的真实材料变形或渐进损伤依据。

新样片均保存固定基准配置、生成入口和适用范围，已完成关键状态、连续视频与六组标签核验及用户视觉效果接受。下一步继续模板与变体准备；参数组合不自动批准连续范围。原生成过程统一保留在 `_work/coverage-expansion-20261008/`，收录核对过程在 `_work/next-baselines-20261008/acceptance-sync/`。

## 爆炸性断裂：搁置

用户否定[0.2广自由段分束视频](_work/explosive-revision-20261008/full_span/composite_full_span_rapid_splitting_baseline_v0_2.mp4)：效果类似毛束断开，不是所要求的爆炸性断裂；补充参考没有足够的实际爆炸性视觉信息。候选已标记拒绝，退出待验收清单，不作为爆炸性模板或已核验覆盖。[JSON](_work/explosive-revision-20261008/full_span/composite_full_span_rapid_splitting_baseline_v0_2.json)保存否定反馈和历史评估，当前主类别回到无法确认。

此前技术检查有效范围仅为网格、运动和编码；独立复核及主Agent对爆炸性视觉效果的通过判断已由用户否定。纵向分裂的补充记录不足以证明爆炸性形态。按用户要求暂停这一款，不再生成或继续调研制作，等待明确恢复指示；原0040真实资料、旧局部型与其他材料成果保留。

## 检查范围与待办

- [x] 将来源、旧版废弃、材料/模式/位置覆盖、15–30秒及本轮反馈保存到DESIGN v1.7。
- [x] 删除本轮错误诊断及过程，核对110条来源标签并实际查看选定参考。
- [x] 用户接受除脱粘片外的六条当前成片，逐条核对校验值后收录；每条均只接受当前视频。
- [x] 两条高分子补全机械连接并检查全机取景、净间隙和原运动保持。
- [x] 两条复材去后板及孤立柱；突断片已接受。
- [x] 颈缩参数化，较弱离散值与默认保持检查完成。
- [x] 已收录视频均完成最终编码/哈希核对、完整解码、独立复核及主Agent实际打开。
- [x] 陶瓷初版拓扑修正、全600帧检查、最终编码、独立复核与实际打开。
- [x] 脱粘片改为断裂与脱粘同时发生；600帧实际检查、最终编码、独立复核和主Agent实际打开完成。
- [x] 用户接受同步脱粘片；已按字节校验值收录，同步本入口和总索引。
- [x] 保存DESIGN v1.8补全基础模板规则；生成三个新增固定候选及可复用入口。
- [x] 三候选实际600帧检查、最终编码、独立复核与主Agent实际打开。
- [x] 用户接受三条新增固定视频的视觉效果；按原候选SHA收录，保留预期/核验标签区别，同步十条总数和材料数量。
- [x] 独立裁决两条未知主模式并核对平板及七条高分子韧性来源，保留证据缺项。
- [x] 金属平板首例修复原生材料连接，完成600帧独立检查、最终编码与主Agent实际打开。
- [x] 用户接受金属平板有限变形首例，按原SHA收录并同步十一条总数。
- [x] 保存用户确认的半脆半韧可见过程判据，更新0014当前类别，保留科学未知与历史核验。
- [x] 爆炸性0.2完成技术检查与主Agent播放，但用户否定视觉效果，撤销类别通过结论。
- [x] 记录0.2候选拒绝并暂停爆炸性生成，不再列为待验收。
- [ ] 补足未确认机制的行为依据并确认适用参数范围，再进行批量变体。

实际求值检查覆盖夹口连接、连通性、事件时序、同一材料段长度/截面/适用体积、断后停止或衰减、间隙与局部穿透；最终编码核对帧数/时间及JSON。独立复核结论适用于各离散定性候选，不是本构标定、微观机制证明、连续参数批准或训练发布。未进行全三角网格自交求解，详细范围与局限记录在JSON。

原批次过程在 `_work/initial-batch-20261008/`，前轮返工/参数检查在 `_work/feedback-revision-20261008/`，同步脱粘重制在 `_work/composite-simultaneous-20261008/`。README和总索引是唯一结果及待办入口。

更新：2026-10-08。
