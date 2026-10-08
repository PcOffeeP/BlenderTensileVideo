# Blender 拉伸实验模拟视频

当前方案：[DESIGN.md](DESIGN.md)（v1.5） · 生成工具：[generator/README.md](generator/README.md) · 唯一机器索引：[outputs/index.json](outputs/index.json) · 工作约定：[AGENTS.md](AGENTS.md)。

## 当前状态

2026-10-08，新的首版已生成 **6条待用户验收候选**，全部为 **20秒、30fps、600帧**，覆盖金属、高分子、复材。已接受数量 **0**，当前基准 **无**；陶瓷来源未确认，因此四类覆盖尚未完成。本轮复用 `codex/rebuild-seeds-from-design` 分支。

用户要求废弃的本轮错误7秒圆棒诊断，其视频、场景、实现与论文调查过程已删除，失效链接与索引已清除。此前收集的原始资料保留。

首版直接参考 `/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data` 中的真实视频及 `video_mapping.csv`、`all_videos_tag.xlsx` 标签，论文不是生成前提。每条目标15–30秒，合理压缩真实实验的加载、变形、破坏和断后观察时间，不把源时间与模拟时间混同。

## 待验收视频

以下均完成技术检查、初版范围独立复核及主 Agent 实际打开播放。视频和同名JSON在工作目录，尚未收录为接受成果。

| 候选 | 来源 | 主要破坏类别 | 模拟位置 | 结果 | 文件（均20秒） |
|---|---|---|---|---|---|
| 金属圆棒颈缩分离 | video_0006 | 韧性断裂 | 标距内 | 完全断裂 | [视频](_work/initial-batch-20261008/metal/ductile/metal_round_ductile_baseline_v1.mp4) · [JSON](_work/initial-batch-20261008/metal/ductile/metal_round_ductile_baseline_v1.json) |
| 金属圆棒小变形突断 | video_0003 | 脆性断裂 | 标距内 | 完全断裂 | [视频](_work/initial-batch-20261008/metal/brittle/metal_round_brittle_baseline_v1.mp4) · [JSON](_work/initial-batch-20261008/metal/brittle/metal_round_brittle_baseline_v1.json) |
| 高分子大伸长断裂 | video_0097 | 韧性断裂 | 标距内 | 完全断裂 | [视频](_work/initial-batch-20261008/polymer/dogbone/polymer_black_dogbone_baseline_v1.mp4) · [JSON](_work/initial-batch-20261008/polymer/dogbone/polymer_black_dogbone_baseline_v1.json) |
| 高分子薄膜夹口根部断裂 | video_0025 | 无法确认 | 夹口根部 | 完全断裂 | [视频](_work/initial-batch-20261008/polymer/film/polymer_yellow_film_grip_root_baseline_v1.mp4) · [JSON](_work/initial-batch-20261008/polymer/film/polymer_yellow_film_grip_root_baseline_v1.json) |
| 复材局部界面脱粘 | video_0020 | 界面脱粘 | 标距内 | 局部破坏但仍连接 | [视频](_work/initial-batch-20261008/composite/debond/composite_interface_debond_baseline_v0_2.mp4) · [JSON](_work/initial-batch-20261008/composite/debond/composite_interface_debond_baseline_v0_2.json) |
| 复材近下夹口突断 | video_0100 | 脆性断裂 | 标距外非根部 | 完全断裂 | [视频](_work/initial-batch-20261008/composite/brittle/composite_brittle_lower_baseline_v0_2.mp4) · [JSON](_work/initial-batch-20261008/composite/brittle/composite_brittle_lower_baseline_v0_2.json) |

来源“齐根断裂”只确定位置，不据此推定薄膜破坏机制。位置按模拟定义的标距归类，来源正式标距未确认。界面脱粘采用两层局部开口的定性建模，真实铺层未知。video_0050标为“其他(无机非)/视频异常”，不能据此当作陶瓷样片。

## 检查范围与待办

- [x] 将用户的来源、旧版废弃、材料/模式/位置覆盖及15–30秒要求保存至DESIGN v1.5。
- [x] 删除本轮错误诊断及其过程，核对110条来源标签并实际查看选定参考的关键状态。
- [x] 生成六条完整模拟视频及同名自包含JSON，记录完整配置/版本、来源、时间映射、观察、假设、未知、预期/核验标签与验收范围。
- [x] 检查实际求值网格的夹口连接、连通性、事件时序、长度/截面/适用体积变化、断后停止/衰减及间隙；核对最终编码和哈希。
- [x] 独立复核并修正复材轴向缩短、高分子夹具出画、金属突断间隙投影遮挡及来源说明串写。主 Agent 逐条打开最终MP4，播放事件阶段并检查初态、加载关键状态和末态。
- [ ] 确认陶瓷来源，补足材料类别覆盖。
- [ ] 用户逐条验收效果与标签；接受后按字节校验值复制到 `outputs/current/<样式>/`，同步本入口和总索引。

独立复核结论仅适用于这六条定性初版候选，不是本构标定、微观机制证明、连续参数范围批准或训练发布。未进行全三角网格自交求解；详细检查范围与局限写在各视频JSON。候选、抽帧、场景与日志统一在 `_work/initial-batch-20261008/`，README与总索引是唯一结果和待办入口。

更新：2026-10-08。
