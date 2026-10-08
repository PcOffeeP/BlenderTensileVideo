# Blender 拉伸实验模拟视频

当前方案：[DESIGN.md](DESIGN.md)（v1.6） · 生成工具：[generator/README.md](generator/README.md) · 唯一机器索引：[outputs/index.json](outputs/index.json) · 工作约定：[AGENTS.md](AGENTS.md)。

## 当前状态

2026-10-08，已接受金属圆棒颈缩分离视频 **1条**；已检查待用户验收 **6条**。本轮已重做两条高分子和两条复材，均为20秒；陶瓷初版已生成并完成检查。复用 `codex/rebuild-seeds-from-design` 分支。仅接受的金属成片收录到 `outputs/current/`，其余保留 `_work/`；批次未验收、未训练发布。

用户要求废弃的本轮错误7秒圆棒诊断，其视频、场景、实现与论文调查过程已删除，失效链接与索引已清除。此前收集的原始资料保留。

直接参考 `/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data` 的真实视频及 `video_mapping.csv`、`all_videos_tag.xlsx`，论文不是生成前提。视频目标15–30秒，本批均20秒，合理压缩真实实验的加载、变形、破坏和断后观察时间；源时间与模拟时间分别记录。

## 当前成果与候选

表内均呈现完全断裂末态，每条JSON记录完整配置/版本、来源、时间映射、观察、假设、未知、预期及核验六组标签和验收范围。高分子和复材的旧候选已被用户反馈撤销，表内及索引只链接此次修正版本。

| 视频 | 来源 | 主要破坏类别 | 模拟位置 | 状态 | 文件（均20秒） |
|---|---|---|---|---|---|
| 金属圆棒颈缩分离 | video_0006 | 韧性断裂 | 标距内 | 已接受 | [视频](outputs/current/metal_round_neck_separation/metal_round_ductile_baseline_v1.mp4) · [JSON](outputs/current/metal_round_neck_separation/metal_round_ductile_baseline_v1.json) |
| 金属圆棒小变形突断 | video_0003 | 脆性断裂 | 标距内 | 待用户验收 | [视频](_work/initial-batch-20261008/metal/brittle/metal_round_brittle_baseline_v1.mp4) · [JSON](_work/initial-batch-20261008/metal/brittle/metal_round_brittle_baseline_v1.json) |
| 高分子大伸长断裂 | video_0097 | 韧性断裂 | 标距内 | 待用户验收 | [视频](_work/feedback-revision-20261008/polymer/dogbone/polymer_black_dogbone_baseline_v2.mp4) · [JSON](_work/feedback-revision-20261008/polymer/dogbone/polymer_black_dogbone_baseline_v2.json) |
| 高分子薄膜夹口根部断裂 | video_0025 | 无法确认 | 夹口根部 | 待用户验收 | [视频](_work/feedback-revision-20261008/polymer/film/polymer_yellow_film_grip_root_baseline_v2.mp4) · [JSON](_work/feedback-revision-20261008/polymer/film/polymer_yellow_film_grip_root_baseline_v2.json) |
| 复材界面脱粘后完全断裂 | video_0020 | 界面脱粘 | 标距内 | 待用户验收 | [视频](_work/feedback-revision-20261008/composite/debond/composite_interface_debond_complete_feedback_v0_3.mp4) · [JSON](_work/feedback-revision-20261008/composite/debond/composite_interface_debond_complete_feedback_v0_3.json) |
| 复材近下夹口突断 | video_0100 | 脆性断裂 | 标距外非根部 | 待用户验收 | [视频](_work/feedback-revision-20261008/composite/brittle/composite_brittle_lower_feedback_v0_3.mp4) · [JSON](_work/feedback-revision-20261008/composite/brittle/composite_brittle_lower_feedback_v0_3.json) |
| 陶瓷小形变横向脆断 | video_0050 | 脆性断裂 | 标距内 | 待用户验收 | [视频](_work/feedback-revision-20261008/ceramic/ceramic_dogbone_brittle_baseline_v1.mp4) · [JSON](_work/feedback-revision-20261008/ceramic/ceramic_dogbone_brittle_baseline_v1.json) |

高分子两条补全夹具、传力杆、移动横梁/导向套、导柱与固定机架的连接，原试样600帧坐标及面拓扑保持；顶梁净间隙已修正。复材两条移除后方大板及孤立机架柱，采用夹具与试样视图；脱粘样片先发展界面开口，再于17秒完成实际分离。位置按照模拟定义的标距归类，来源正式标距未确认。薄膜来源“齐根断裂”只确定位置，机制仍为“无法确认”。

video_0050陶瓷身份由用户确认；原表“其他(无机非)/视频异常”保持。源视频可见逐渐发展的横向裂纹，末态完整分离和具体事件时间缺少直接证据。陶瓷初版的完整脆断为作者定性扩展，材料牌号、微观机制及本构参数未知；不能当成源视频逐帧复现。

金属增加颈缩控制 `--neck-local-stretch-amplitude`，默认4.0保留已接受效果，局部轴向伸长、截面及加载端位置耦合计算。较弱2.0仅生成关键状态并核验；默认值与原场景38帧比对通过浮点容差。工程守卫 `0 < A ≤ 4.0` 不表示连续范围已批准，接受的原成片仍为1.0.1配置。

## 检查范围与待办

- [x] 将来源、旧版废弃、材料/模式/位置覆盖、15–30秒及本轮反馈保存到DESIGN v1.6。
- [x] 删除本轮错误诊断及过程，核对110条来源标签并实际查看选定参考。
- [x] 用户接受金属颈缩成片，核对校验值后收录；仅单条视频接受。
- [x] 两条高分子补全机械连接并检查全机取景、净间隙和原运动保持。
- [x] 两条复材去后板及孤立柱，脱粘后完全断裂已重做。
- [x] 颈缩参数化，较弱离散值与默认保持检查完成。
- [x] 本轮五条新视频最终编码/哈希核对、完整解码、独立复核及主Agent实际打开完成。
- [x] 陶瓷初版拓扑修正、全600帧检查、最终编码、独立复核与实际打开。
- [ ] 用户逐条验收效果与标签；接受后按字节校验值复制到 `outputs/current/<样式>/`，同步本入口和总索引。

实际求值检查覆盖夹口连接、连通性、事件时序、同一材料段长度/截面/适用体积、断后停止或衰减、间隙与局部穿透；最终编码核对帧数/时间及JSON。独立复核结论适用于各离散定性候选，不是本构标定、微观机制证明、连续参数批准或训练发布。未进行全三角网格自交求解，详细范围与局限记录在JSON。

原批次过程在 `_work/initial-batch-20261008/`，本轮返工/参数检查在 `_work/feedback-revision-20261008/`。README和总索引是唯一结果及待办入口。

更新：2026-10-08。
