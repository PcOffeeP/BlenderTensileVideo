# Blender 拉伸实验模拟视频

当前方案：[DESIGN.md](DESIGN.md)（v1.12） · 生成工具：[generator/README.md](generator/README.md) · 唯一机器索引：[outputs/index.json](outputs/index.json) · 工作约定：[AGENTS.md](AGENTS.md)。

## 当前状态

2026-10-09，当前 **二十七条20秒视频已由用户接受并收录，包括十一条基础视频、九条第一阶段单参数变体和七条组合视频**。已接受视频分布为金属7条、高分子10条、复材8条、陶瓷2条。新金属平板按原候选SHA收录，视频字节保持。高分子半脆半韧已按用户补充的项目视觉判据确认当前样片；新版复材广自由段分束候选已被用户否定，爆炸性断裂生成暂停；旧局部型及其他已接受视频继续保留。样式与连续参数范围、训练发布分别记录，六组生成/验收标签不替代下游训练字段。

用户要求废弃的本轮错误7秒圆棒诊断，其视频、场景、实现与论文调查过程已删除，失效链接与索引已清除。此前收集的原始资料保留。

直接参考 `/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data` 的真实视频及 `video_mapping.csv`、`all_videos_tag.xlsx`，论文不是生成前提。视频目标15–30秒，当前成片均20秒，按来源重定时：较长实验过程压缩，短来源的阶段延长；分别呈现加载、变形、破坏和断后观察；源时间与模拟时间分别记录。

## 当前成果

2026-10-09，用户确认第一阶段围绕断前伸长、金属颈缩、同类别内破坏位置、事件时序与同步脱粘展开离散变体设计。关键规则归入全局DESIGN，候选值、测量定义及实现检查要求见 [第一阶段断裂参数专项设计](docs/fracture-variation-stage1.md)。参数入口和九条单参数变体已完成制作及适用检查，均为20秒、30fps、600帧，独立复核及主Agent成片查看已完成，用户以“可以，没问题”接受这九条具体视频的效果与标签，已按原候选SHA收录；该单参数阶段收录后共二十条，随后七条组合也已接受，当前共二十七条。样式、连续范围和训练发布仍未批准，爆炸性生成继续暂停。

### 首批新增训练视频设计

[首批新增训练视频设计](docs/training-batch1-design.md)用于下一阶段制作与下游输入准备。用户已确认新增约60条、按有效行为空间分配（金属20、高分子28、复材10、陶瓷2），以及在已接受端点之间选取新的离散档位。文档列出具体候选、资格／组合检查、逐片接受与标签交付边界。用户已于2026-10-09授权开始实施；有限参数入口与冻结配置已完成，107个配置的作者侧检查已完成；隔离检查已完成：107个当前节点中81项通过、10项失败、16项因失败依赖未执行；25项旧源均实际检查600帧，20项通过、5项失败。已编码38条候选，逐片主观看及独立材料／标签复核已完成；38条最终JSON及实际归档独立复验均已通过，全部待用户逐条接受效果与标签。执行与检查证据保存在`_work/training-batch1-20261009/`，已生成候选的路径和当前状态记录在index中。现有27条作为参考，不靠重复渲染计入新增数量；实际交付由通过检查与接受的配置决定。

当前检查阻塞：狗骨旧0.85配置及部分新增资格配置未通过严格负间隙门禁，相关候选暂不渲染；既有浮点累积残差的诊断与限定事件帧处理提案已完成独立复核，容差与几何尚未改变。未修改的薄膜分支同样保留失败，不计入新增60条。其余模板的38条候选已完成适用检查。批量交叉积计算已通过独立等价审查，已在隔离执行目录启用，已对适用节点完成实际600帧检查（当前91项、旧源25项，另16项依赖阻断未执行），旧证据与两条陶瓷待验收文件保留。是否采用限定首断帧精度认证等待用户确认；金属韧断两组旧版回归另因实际体积上界约1.00636超过冻结门限1.0052而失败，已完成门限依据与测量记录独立核对；其12条候选暂被完整模板回归阻断。连同狗骨10条，保持当前门禁时本批上限为38条，另22条严格阻塞。[金属体积独立复核](_work/training-batch1-20261009-fastcheck/review/metal_volume_review.json)确认是实际开口区几何近似，未发现测量接线问题；是否允许确切历史回归例外或改变体积判据等待用户确认。旧源25项已完成实际600帧检查，20项通过、5项失败；当前检查与4路渲染已经结束；38条均完成主观看，60组所需精确差异参照均已由独立复核逐组查看。

2026-10-10，当前已编码38条（陶瓷2、金属脆断8、高分子脆断8、半脆半韧10、复材脆断4、同步脱粘6），均为20秒、600帧、30fps且完整解码通过；38条均完成主Agent逐片观看、独立材料／标签复核以及最终JSON和实际归档独立复验，全部列入待用户逐条验收。金属与半脆半韧采用固定逐配对证据的v2报告完成实际JSON应用及归档复核，高分子脆断实际归档复核也已通过；此前独立reviewer账号用量限制导致的26条元数据收尾阻塞已解除。所有旧报告与证明保留，复材曾发现的共享汇总依赖缺口已通过v2固定逐配对证据修复。六组核验标签与整段视频V4.1四字段标签分别保存在JSON和index中；未来切片仍须按实际输入重新标注。

首批当前38条待验收（均20秒、600帧，未收录current、未训练发布；以下逐条打开视频与JSON）：

| 候选 | 核验标签 | 文件 |
|---|---|---|
| 陶瓷13秒失贯通 | 陶瓷／完全断裂／脆性断裂／标距内／无夹持与拍摄异常 | [视频](_work/training-batch1-20261009/execution/runs/ceramic_fafb6d038402/321ad3776c4157e1/ceramic_fafb6d038402.mp4) · [JSON](_work/training-batch1-20261009/execution/runs/ceramic_fafb6d038402/321ad3776c4157e1/ceramic_fafb6d038402.json) |
| 陶瓷15秒失贯通 | 陶瓷／完全断裂／脆性断裂／标距内／无夹持与拍摄异常 | [视频](_work/training-batch1-20261009/execution/runs/ceramic_54c9123982ca/a99ea32b123b992f/ceramic_54c9123982ca.mp4) · [JSON](_work/training-batch1-20261009/execution/runs/ceramic_54c9123982ca/a99ea32b123b992f/ceramic_54c9123982ca.json) |
| 复材脆断 40de05bc8db6 | 复材／完全断裂／脆性断裂／标距外非根部／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_40de05bc8db6/cf31a152fc1a013c/composite_brittle_40de05bc8db6.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_40de05bc8db6/cf31a152fc1a013c/composite_brittle_40de05bc8db6.json) |
| 复材脆断 71add4d43545 | 复材／完全断裂／脆性断裂／标距外非根部／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_71add4d43545/4b01eabc2cde4b14/composite_brittle_71add4d43545.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_71add4d43545/4b01eabc2cde4b14/composite_brittle_71add4d43545.json) |
| 复材脆断 85e1faca3a2f | 复材／完全断裂／脆性断裂／标距外非根部／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_85e1faca3a2f/ca57a89fe68b9e1b/composite_brittle_85e1faca3a2f.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_85e1faca3a2f/ca57a89fe68b9e1b/composite_brittle_85e1faca3a2f.json) |
| 复材脆断 f8c38a77a63d | 复材／完全断裂／脆性断裂／标距外非根部／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_f8c38a77a63d/bf0ef0b2a0346004/composite_brittle_f8c38a77a63d.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/composite_brittle_f8c38a77a63d/bf0ef0b2a0346004/composite_brittle_f8c38a77a63d.json) |
| 同步脱粘 19ad315937d9 | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_19ad315937d9/ce8c4c5307275b33/debond_19ad315937d9.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_19ad315937d9/ce8c4c5307275b33/debond_19ad315937d9.json) |
| 同步脱粘 3a83e6589f3c | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_3a83e6589f3c/750b8d5d527eb7b6/debond_3a83e6589f3c.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_3a83e6589f3c/750b8d5d527eb7b6/debond_3a83e6589f3c.json) |
| 同步脱粘 633abced1e80 | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_633abced1e80/87ef6945bd15b32e/debond_633abced1e80.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_633abced1e80/87ef6945bd15b32e/debond_633abced1e80.json) |
| 同步脱粘 9a6e9873f857 | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_9a6e9873f857/29cb36efc2fe9c8c/debond_9a6e9873f857.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_9a6e9873f857/29cb36efc2fe9c8c/debond_9a6e9873f857.json) |
| 同步脱粘 f1b9bd026fc6 | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_f1b9bd026fc6/cdd6f60e24205d15/debond_f1b9bd026fc6.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_f1b9bd026fc6/cdd6f60e24205d15/debond_f1b9bd026fc6.json) |
| 同步脱粘 f8acebcca850 | 复材／完全断裂／界面脱粘／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/debond_f8acebcca850/29b1720f7c8cfa14/debond_f8acebcca850.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/debond_f8acebcca850/29b1720f7c8cfa14/debond_f8acebcca850.json) |
| 金属脆断 24b9f8453ffd | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_24b9f8453ffd/299b1b60ab02fa6d/metal_brittle_24b9f8453ffd.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_24b9f8453ffd/299b1b60ab02fa6d/metal_brittle_24b9f8453ffd.json) |
| 金属脆断 5208fef67de7 | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_5208fef67de7/e0d63d0994544642/metal_brittle_5208fef67de7.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_5208fef67de7/e0d63d0994544642/metal_brittle_5208fef67de7.json) |
| 金属脆断 8fd177bc37cd | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_8fd177bc37cd/afbfd0a64e7ecd6c/metal_brittle_8fd177bc37cd.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_8fd177bc37cd/afbfd0a64e7ecd6c/metal_brittle_8fd177bc37cd.json) |
| 金属脆断 95bf83c84c0a | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_95bf83c84c0a/630254443bf4d0f8/metal_brittle_95bf83c84c0a.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_95bf83c84c0a/630254443bf4d0f8/metal_brittle_95bf83c84c0a.json) |
| 金属脆断 c3f0c995c8ef | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_c3f0c995c8ef/f6429b6982180419/metal_brittle_c3f0c995c8ef.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_c3f0c995c8ef/f6429b6982180419/metal_brittle_c3f0c995c8ef.json) |
| 金属脆断 cc100241b5f7 | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_cc100241b5f7/d57ef5d42534ee45/metal_brittle_cc100241b5f7.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_cc100241b5f7/d57ef5d42534ee45/metal_brittle_cc100241b5f7.json) |
| 金属脆断 d113c4e01c83 | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_d113c4e01c83/139b32c24bc6bc14/metal_brittle_d113c4e01c83.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_d113c4e01c83/139b32c24bc6bc14/metal_brittle_d113c4e01c83.json) |
| 金属脆断 dda4b5e6e727 | 金属／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_dda4b5e6e727/0ce641ad891eda47/metal_brittle_dda4b5e6e727.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/metal_brittle_dda4b5e6e727/0ce641ad891eda47/metal_brittle_dda4b5e6e727.json) |
| 高分子脆断 527d847f2741 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_527d847f2741/c9037aa8bc8a9b75/polymer_brittle_527d847f2741.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_527d847f2741/c9037aa8bc8a9b75/polymer_brittle_527d847f2741.json) |
| 高分子脆断 7c88eeeae51f | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_7c88eeeae51f/adfb7bbf8e460c61/polymer_brittle_7c88eeeae51f.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_7c88eeeae51f/adfb7bbf8e460c61/polymer_brittle_7c88eeeae51f.json) |
| 高分子脆断 b0cd99f7ae30 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_b0cd99f7ae30/303aff50310f92bc/polymer_brittle_b0cd99f7ae30.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_b0cd99f7ae30/303aff50310f92bc/polymer_brittle_b0cd99f7ae30.json) |
| 高分子脆断 b9ab8a238e19 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_b9ab8a238e19/513abd4d2ec8acf4/polymer_brittle_b9ab8a238e19.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_b9ab8a238e19/513abd4d2ec8acf4/polymer_brittle_b9ab8a238e19.json) |
| 高分子脆断 bcfe3a307376 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_bcfe3a307376/e1783fa01c4f150d/polymer_brittle_bcfe3a307376.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_bcfe3a307376/e1783fa01c4f150d/polymer_brittle_bcfe3a307376.json) |
| 高分子脆断 e2c15b3c1473 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_e2c15b3c1473/44d4b2b618c005d7/polymer_brittle_e2c15b3c1473.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_e2c15b3c1473/44d4b2b618c005d7/polymer_brittle_e2c15b3c1473.json) |
| 高分子脆断 ea23f4e39317 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_ea23f4e39317/aee88dd89417680a/polymer_brittle_ea23f4e39317.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_ea23f4e39317/aee88dd89417680a/polymer_brittle_ea23f4e39317.json) |
| 高分子脆断 f89aa7bc8961 | 高分子／完全断裂／脆性断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_f89aa7bc8961/5d3bd34030557d9f/polymer_brittle_f89aa7bc8961.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/polymer_brittle_f89aa7bc8961/5d3bd34030557d9f/polymer_brittle_f89aa7bc8961.json) |
| 高分子半脆半韧 2a9499713a2b | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_2a9499713a2b/fdac8cf6db4b1b29/mixed_2a9499713a2b.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_2a9499713a2b/fdac8cf6db4b1b29/mixed_2a9499713a2b.json) |
| 高分子半脆半韧 3568deb2ca33 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_3568deb2ca33/a598f754f98dbcae/mixed_3568deb2ca33.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_3568deb2ca33/a598f754f98dbcae/mixed_3568deb2ca33.json) |
| 高分子半脆半韧 474c4c10ff01 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_474c4c10ff01/cbe93e29ae240cfe/mixed_474c4c10ff01.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_474c4c10ff01/cbe93e29ae240cfe/mixed_474c4c10ff01.json) |
| 高分子半脆半韧 6bd6ad919f7f | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_6bd6ad919f7f/cde2e69aa79dea52/mixed_6bd6ad919f7f.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_6bd6ad919f7f/cde2e69aa79dea52/mixed_6bd6ad919f7f.json) |
| 高分子半脆半韧 8e505bb139b5 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_8e505bb139b5/0ae78bbe2cbcc2a9/mixed_8e505bb139b5.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_8e505bb139b5/0ae78bbe2cbcc2a9/mixed_8e505bb139b5.json) |
| 高分子半脆半韧 b6dd4440bb01 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_b6dd4440bb01/d68545a590accaf5/mixed_b6dd4440bb01.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_b6dd4440bb01/d68545a590accaf5/mixed_b6dd4440bb01.json) |
| 高分子半脆半韧 c25215a9fc08 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_c25215a9fc08/b5d0e4175e96743c/mixed_c25215a9fc08.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_c25215a9fc08/b5d0e4175e96743c/mixed_c25215a9fc08.json) |
| 高分子半脆半韧 d78ee0af8f98 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_d78ee0af8f98/9b9d7e6e89068b74/mixed_d78ee0af8f98.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_d78ee0af8f98/9b9d7e6e89068b74/mixed_d78ee0af8f98.json) |
| 高分子半脆半韧 e4b70b9f11d1 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_e4b70b9f11d1/3a7403d5ea862930/mixed_e4b70b9f11d1.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_e4b70b9f11d1/3a7403d5ea862930/mixed_e4b70b9f11d1.json) |
| 高分子半脆半韧 f22a4a698822 | 高分子／完全断裂／半脆半韧断裂／标距内／无／无 | [视频](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_f22a4a698822/02de1d955cdbe03f/mixed_f22a4a698822.mp4) · [JSON](_work/training-batch1-20261009-fastcheck/execution/runs/mixed_f22a4a698822/02de1d955cdbe03f/mixed_f22a4a698822.json) |

材料与微观机制、本构参数、来源正式标距及精确首次肉眼可判分离仍按JSON记录未知。部分离散差异在原生分辨率下细微，未保证下游降采样可区分或训练收益。原27条已接受视频与JSON本次逐字节校验保持。

### 第一阶段已接受组合视频

按 [组合验证专项说明](docs/fracture-coupling-validation.md) 完成七条组合样片。各模板选定单时间先完成600帧技术资格，七组合另行完成600帧实际检查、最终编码、独立复核及主Agent成片查看；用户于2026-10-09以“可以，都没问题”接受这七条具体20秒视频的效果与标签，已按原候选SHA收录到current。资格检查不表示单时间视频已接受，组合接受不批准样式或连续范围。原二十条成片与同名JSON保持。

| 已接受组合 | 参数组合 | 类别／位置 | 文件（20秒） |
|---|---|---|---|
| 金属韧断：较弱颈缩＋12秒 | A=2；12秒 | 韧性断裂／标距内 | [视频](outputs/current/metal_round_ductile/metal_round_ductile_coupled_a2_time12_v1.mp4) · [JSON](outputs/current/metal_round_ductile/metal_round_ductile_coupled_a2_time12_v1.json) |
| 金属脆断：位置偏移＋15秒 | 材料中心+0.75；15秒 | 脆性断裂／标距内 | [视频](outputs/current/metal_round_brittle/metal_round_brittle_coupled_center_p075_time15_v1.mp4) · [JSON](outputs/current/metal_round_brittle/metal_round_brittle_coupled_center_p075_time15_v1.json) |
| 高分子韧断：较小伸长＋17秒 | 伸长增量×0.85；17秒 | 韧性断裂／标距内 | [视频](outputs/current/polymer_black_flexible_dogbone/polymer_dogbone_coupled_stretch085_time17_v1.mp4) · [JSON](outputs/current/polymer_black_flexible_dogbone/polymer_dogbone_coupled_stretch085_time17_v1.json) |
| 高分子脆断：位置偏移＋12秒 | 材料分数0.55；12秒 | 脆性断裂／标距内 | [视频](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_brittle_coupled_position055_time12_v1.mp4) · [JSON](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_brittle_coupled_position055_time12_v1.json) |
| 高分子半脆半韧：较大伸长＋15秒 | 伸长增量×1.15；15秒 | 半脆半韧断裂／标距内 | [视频](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_mixed_coupled_stretch115_time15_v1.mp4) · [JSON](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_mixed_coupled_stretch115_time15_v1.json) |
| 复材脆断：低位偏移＋12秒 | 材料中心−1.95；12秒 | 脆性断裂／标距外非根部 | [视频](outputs/current/composite_brittle_lower/composite_brittle_coupled_center_minus195_time12_v1.mp4) · [JSON](outputs/current/composite_brittle_lower/composite_brittle_coupled_center_minus195_time12_v1.json) |
| 复材同步脱粘：长度＋开口＋15秒 | 长度×0.8；开口×1.2；15秒 | 界面脱粘／标距内 | [视频](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_coupled_length080_opening120_time15_v1.mp4) · [JSON](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_coupled_length080_opening120_time15_v1.json) |

[组合视频V4.1标签预览](_work/coupled-stage1-20261009/labels.v4_1.preview.jsonl)包含七条整段20秒的四字段标签payload，沿用实际下游契约与验证器，状态为`user_accepted_label_preview_not_training_release`，路径指向current；未来切片按实际输入重新标注，当前预览未作为训练集发布。六组模拟标签、配置、基准关联、资格与组合实测、来源、作者假设、科学未知及验收边界保存在各同名JSON。

[组合独立复核](_work/coupled-stage1-20261009/review/coupled_final_review.md)限于所绑定七条离散定性视频。金属的原生拓扑／几何重合连接区别、体积几何近似、精确首次肉眼可判分离未知以及未进行通用三角自交穷尽／本构标定的限制保持。高分子17秒组合的断后运动须在20秒前停止，复材同步脱粘与断裂同帧开始，组合实测详见JSON。

### 第一阶段已接受单参数变体

| 已接受变体 | 单一变化 | 主要类别／位置 | 文件（20秒） |
|---|---|---|---|
| 金属韧断：较弱颈缩 | A：4→2 | 韧性断裂／标距内 | [视频](outputs/current/metal_round_ductile/metal_round_ductile_stage1_a2_v1.mp4) · [JSON](outputs/current/metal_round_ductile/metal_round_ductile_stage1_a2_v1.json) |
| 金属脆断：标距内偏移 | 破坏中心：0→+0.75 | 脆性断裂／标距内 | [视频](outputs/current/metal_round_brittle/metal_round_brittle_stage1_center_p075_v1.mp4) · [JSON](outputs/current/metal_round_brittle/metal_round_brittle_stage1_center_p075_v1.json) |
| 高分子韧断：较小伸长 | 伸长增量×0.85 | 韧性断裂／标距内 | [视频](outputs/current/polymer_black_flexible_dogbone/polymer_black_dogbone_stage1_stretch085_v1.mp4) · [JSON](outputs/current/polymer_black_flexible_dogbone/polymer_black_dogbone_stage1_stretch085_v1.json) |
| 高分子脆断：标距内偏移 | 破坏材料分数：0.50→0.55 | 脆性断裂／标距内 | [视频](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_brittle_stage1_position055_v1.mp4) · [JSON](outputs/current/polymer_pale_green_brittle_flat_strip/polymer_brittle_stage1_position055_v1.json) |
| 高分子半脆半韧：较大伸长 | 伸长增量×1.15 | 半脆半韧断裂／标距内 | [视频](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_mixed_stage1_stretch115_v1.mp4) · [JSON](outputs/current/polymer_finite_deformation_oblique_rupture/polymer_mixed_stage1_stretch115_v1.json) |
| 复材脆断：低位偏移 | 破坏中心：−1.83→−1.95 | 脆性断裂／标距外非根部 | [视频](outputs/current/composite_brittle_lower/composite_brittle_stage1_position_minus012_v1.mp4) · [JSON](outputs/current/composite_brittle_lower/composite_brittle_stage1_position_minus012_v1.json) |
| 复材同步脱粘：较短范围 | 脱粘长度×0.8 | 界面脱粘／标距内 | [视频](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_stage1_length080_v1.mp4) · [JSON](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_stage1_length080_v1.json) |
| 复材同步脱粘：较大开口 | 界面开口×1.2 | 界面脱粘／标距内 | [视频](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_stage1_opening120_v1.mp4) · [JSON](outputs/current/composite_interface_debond_simultaneous_complete/composite_debond_stage1_opening120_v1.json) |
| 陶瓷脆断：较早断裂 | 最终失去贯通：16→12秒 | 脆性断裂／标距内 | [视频](outputs/current/ceramic_dogbone_brittle/ceramic_brittle_stage1_time12_v1.mp4) · [JSON](outputs/current/ceramic_dogbone_brittle/ceramic_brittle_stage1_time12_v1.json) |

每条同名JSON区分完整配置、来源、作者假设、实际测量、六组预期／核验标签和验收范围。九条已收录到`outputs/current/<style_id>/`，原`_work`视频和检查证据保留；每条仅接受当前视频效果与标签，不批准样式或连续参数范围。复材脱粘与断裂仍同时开始。半脆半韧伸长测量扣除裂缝开口，最后连接前增量比例约1.14999934。

[整段视频V4.1标签预览](_work/fracture-stage1-20261009/labels.v4_1.preview.jsonl)已对照实际下游`pipeline/contracts/tensile_vlm_v4_1.json`核验字段和值，并通过其既有验证器：`clip_state`、`fracture_mechanism`、`fracture_site`、`special_case`。这些20秒整段均包含破坏事件，预览状态为“发生断裂”。材料身份与精确事件时间仍保存在模拟JSON；预览状态为`user_accepted_label_preview_not_training_release`，路径已指向current；预览不是已发布训练集，未来切片须按实际区间重新标注，未更改切片规则或绑定训练prompt发布版本。

新入口默认回归覆盖各适用分支600帧；九条变体各完成实际求值检查及最终完整解码。[独立复核](_work/fracture-stage1-20261009/review/stage1_final_review.md)限定于这些离散定性视频。金属圆棒沿用已接受基准的重合界面几何连接，几何焊接检查与原生共享索引连接分别记录；不将其写成原生单网格连接。没有进行一般三角网格自交求解或本构标定。高分子大伸长的1.15倍与原位置、时间及固定相机组合因机架出框被阻断，未生成可用候选；这不影响另一模板的半脆半韧1.15倍。

### 已接受基础视频

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

金属颈缩控制 `--neck-local-stretch-amplitude` 默认4.0保留已接受效果，局部轴向伸长、截面及加载端位置耦合计算。第一阶段较弱2.0的完整视频已由用户接受并收录，新默认与已接受烘焙场景600帧坐标、拓扑及夹具保持一致。工程守卫 `0 < A ≤ 4.0` 不表示连续范围已批准，接受的原成片仍为1.0.1配置。

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
- [x] 确认第一阶段断裂参数设计及全局／专项文档分层规则。
- [x] 按专项设计补齐适用参数入口，完成固定基准600帧回归与九条单参数候选的逐帧检查、编码、独立复核和主Agent成片查看。
- [x] 输出与实际下游V4.1接口相符的整段标签预览，保持六组模拟标签与训练字段区分。
- [x] 用户接受九条第一阶段单参数视频效果与标签，按原候选SHA收录并同步二十条总数、材料数量及标签预览路径。
- [x] 七条离散组合完成单时间资格、组合实际检查、编码、独立复核及主Agent成片查看。
- [x] 用户接受七条组合视频效果与标签，按原候选SHA收录并同步二十七条总数、材料数量及标签预览路径。
- [x] 确认首批新增约60条的设计取舍，保存断裂参数候选、配比、检查及下游输入准备边界。
- [ ] 按首批专项设计进入实施规划与制作，逐片验收后交付数据源；下游输入适配及训练发布沿用现有流程。
- [ ] 补足未确认机制的行为依据；不以参数设计确认替代适用范围核验或训练发布。

实际求值检查覆盖夹口连接、连通性、事件时序、同一材料段长度/截面/适用体积、断后停止或衰减、间隙与局部穿透；最终编码核对帧数/时间及JSON。独立复核结论适用于各离散定性候选，不是本构标定、微观机制证明、连续参数批准或训练发布。未进行全三角网格自交求解，详细范围与局限记录在JSON。

原批次过程在 `_work/initial-batch-20261008/`，前轮返工/参数检查在 `_work/feedback-revision-20261008/`，同步脱粘重制在 `_work/composite-simultaneous-20261008/`。README和总索引是唯一结果及待办入口。

更新：2026-10-09。
