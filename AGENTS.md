# 项目工作约定

## 协作与 Git

1. 按用户最新指示和已确认的 `docs/DESIGN.md` 执行。授权范围内的实现自行决定。
2. 需要改变项目范围、架构、标签含义、数据流或验收规则，或执行不可逆迁移时，先确认未决事项。
3. 开工前查看分支和已有差异，保留他人修改及已授权的删除、迁移。按任务范围提交，说明验证结果，提交说明包含“以上commit由ai生成。”。分支创建、PR 审查与清理按下方「Git 协作与 PR 审查流」执行。

<!-- git-pr-workflow:start -->
## Git 协作与 PR 审查流

- **主线与远程**：本仓库长期主线分支为 `main`，PR 审查远程为 `github`（PR 流程基线 tag：`pr-workflow-baseline-20261120`）。
- **开工前置动作**：每个独立任务开始前先运行 `bash scripts/sync_and_clean.sh`（自动拉取最新 `github/main`、同步主工作区并安全清理已合并的干净 `work/*` 残留），再显式从最新远端主线创建独立 worktree 与任务分支：
  ```bash
  git worktree add --no-track ../BlenderTensileVideo-<线名> -b work/<线名> github/main
  ```
  不要在主工作区切换分支，同一 worktree 内不得并行两个写入者。
- **交付与 PR**：在任务分支完成开发并跑通本项目准入检查（`generator/*.py` 语法校验及 `datasets/`、`review/` JSON 合法性校验；涉及视频制作须完成实际画面核对）后，推送 `work/<线名>` 到 `github` 并创建指向 `main` 的 PR（`gh pr create --base main`，严格按 `.github/PULL_REQUEST_TEMPLATE.md` 填写）。
- **权限红线**：允许 Agent 推送自己的 `work/*` 任务分支并创建/更新 PR；**严禁** push `main`，**严禁**自行合并 PR，也不要本地直接合并回主线。
- **合并与自动清理**：PR 统一由用户在远端审查并通过所有 Required Status Checks 后以 **Create a merge commit** 合并（保留“任务信封”合并节点）；远程 `work/*` 分支在 PR 合并后自动删除。对已通过 Merge Commit 合入 `github/main` 且工作树完全干净的本地 `work/*` 分支及对应 worktree，已永久预授权 Agent 通过 `bash scripts/sync_and_clean.sh` 自动清理，无需逐次请示；未合并、含未提交改动或用途不明的分支严禁删除。

### 共享关键资源防并发规则（Draft PR 占坑）

- **受保护共享路径 / 外部资源**：`datasets/*/manifest.json`（正式样本清单与版本边界）、`datasets/*/labels.*`（标签表）、以及共享的 `_work/` 渲染输出目录。
- **开工前探针**：准备修改上述共享路径或操作共享外部资源前，必须先检查在途 PR：
  ```bash
  gh pr list --state open --json number,headRefName,title,isDraft,labels,files
  ```
  若已有在途 PR 正在修改同一共享资源，须等待其合并或关闭后再动手，不得并发写入或基于过期清单执行收录。
- **先占坑再干活**：确认空闲后，先在自己的 `work/*` 分支新建变更声明 `docs/changes/<日期>-<线名>-<对象>.md`（写明意图、涉及文件/资源、时间窗口、备份与回滚方式），立刻提交推送并创建一个 **Draft PR** 占坑：
  ```bash
  git push -u github work/<线名>
  gh pr create --draft --base main --title "wip(lock): <简述>" --body-file docs/changes/<日期>-<线名>-<对象>.md
  ```
- **完工转正与自动释放**：修改完成并在变更单中追加「已完成 + 实际结果」后，推送到同一分支并将 Draft PR 转为 Ready for review（`gh pr ready`）；PR 合并或关闭后占坑自动释放。
<!-- git-pr-workflow:end -->

## 项目入口

- 先读根 `README.md`。正式样本的成员、有效标签及修订依据查 `datasets/<版本>/manifest.json`，候选审核状态查 `review/<批次>/<id>.json`。
- 制作与返工放在 `_work/<任务>/`。送审时将 MP4 与同名 JSON 放入 `review/<批次>/`。清理前核对授权、文件占用和引用，保留原始实验资料及必要的复核依据。

## 制作、复核与收录

- 按 `docs/DESIGN.md` 选择与材料、试样和拉伸行为匹配的参数搭配，分别记录观察、建模假设和未知项。主 Agent 须实际查看最终编码视频并核对关键状态。
- 材料行为、科学准确性与标签依据由制作方以外的复核者检查。未完成的项目标为待复核。用户按设计文档“标签判定与人工验收”确认画面和标签，两项结论分别记录。
- 按用户确认的用途收录候选，保留已交付版本的成员边界。收录时按稳定 ID 核对成片、元数据、校验值、版本清单和标签表。用于整片验证的授权仅覆盖该用途。
