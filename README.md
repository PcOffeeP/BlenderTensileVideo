# Blender 拉伸实验模拟视频

用 Blender 制作金属、高分子、复材和陶瓷试样的拉伸视频，为多模态模型提供可追溯的整片样本。每条样片记录可见行为、生成配置、来源、作者假设和标签确认范围。

## 使用正式数据

[video-V1 数据包](datasets/video-V1/) 收录用户于 2026-10-10 确认的 **65 条验证视频**。每条 20 秒、30 fps、600 帧，包含高分子 28 条、复材 18 条、金属 15 条、陶瓷 4 条。

| 要做什么 | 打开哪里 |
|---|---|
| 读取标签、按 ID 找视频 | [labels.csv](datasets/video-V1/labels.csv) 的每行对应 [videos/](datasets/video-V1/videos/) 中的 `<id>.mp4` |
| 查看某条样本的来源、参数、事件和历史判断 | [metadata/](datasets/video-V1/metadata/) 中的 `<id>.json` |
| 验证文件、查验收范围和有效标签 | [manifest.json](datasets/video-V1/manifest.json) 保存成员、相对路径、SHA-256 和标签修订依据 |

CSV 按参考表 `annotation-table-full.csv` 的 28 列导出。断裂时间点以秒计，前后帧从 0 起，对应试样在模拟中最终失去贯通连接的事件；清晰度为成片的宽×高。逐片现象的依据与未知项见[标签导出规则](generator/README.md#统一视频标注导出)。27 条有逐片接受记录，另 38 条经复核后随整批确认。金属平板及薄膜根部两条的有效断裂模式已于 2026-11-10 确认为韧性断裂。V1 的用途为整片验证，切片标签及训练发布另行判定。

V1 的[单参数设计](docs/history/video-v1/fracture-variation-stage1.md)、[组合验证设计](docs/history/video-v1/fracture-coupling-validation.md)和[首批新增计划](docs/history/video-v1/training-batch1-design.md)已归档到 `docs/history/video-v1/`。历史元数据中指向这三篇文档的旧路径，可按原文件名在归档目录查阅。

## 审核候选

打开 [review/](review/) 即可看片，每条 MP4 旁的同名 JSON 记录其审核状态。当前共 12 条：

| 批次 | 待确认事项 |
|---|---|
| [完整场景补样，3 条](review/supplement-20261114/) | 双侧开裂和未夹紧的画面已认可，五类标签待审。爆炸性断裂的画面与标签均待审。 |
| [独立合成批次，8 条](review/independent-batch-20261114/) | 4 条脆断与 4 条韧断的画面、标签待审，尤其留意首帧已断及末帧才断的可见线索。 |
| [独立陶瓷试片，1 条](review/independent-pilot-20261114/) | 陶瓷脆断的画面、标签待审。同批旧金属逐侧撕裂方案已否决。 |

## 制作与收录

1. **选样。** 按[项目设计](docs/DESIGN.md)确定用途、适用的拉伸行为及参数搭配，再从[参数与测量规范](docs/video-generation-parameters.md)选择基准、变化项、固定条件和检查方法。
2. **制作。** 按[生成器说明](generator/README.md)在 `_work/<任务>/` 生成、检查和返工。保留适用的几何测量、时序和最终编码证据。
3. **送审。** 将可观看的 MP4 和同名 JSON 放入 `review/<批次>/`，分别记录技术核验、画面及标签确认。
4. **收录。** 用户确认用途后，将配对文件纳入指定版本的数据集，核验校验值并重导标签。已交付 V1 的成员固定。旧批次另有 22 个拟生成配置受几何检查阻断，若重启，先处理狗骨间隙和金属韧断体积回归。

从项目根目录运行 `python3 generator/export_video_labels.py --summary` 可查询当前数量。独立交接时复制整个数据包即可；如需重导，再使用[标签导出器](generator/README.md#统一视频标注导出)。项目协作见 [AGENTS.md](AGENTS.md)。
