# 安全扫描与静态检查记录

检查日期：2026-11-18（Asia/Shanghai）。本次仅生成说明与脱敏汇总，未修改业务代码、配置、扫描规则或白名单，未启动、重置服务，也未验证任何凭据是否有效。

## 结论

| 检查 | 范围 | 结果 |
| --- | --- | --- |
| Gitleaks 暂存区 | 检查时已暂存的 Git 差异 | 通过：0 项，退出码 0 |
| Gitleaks Git 历史 | 本地仓库全部 3 个提交；非浅克隆 | 未通过：1 项，退出码 1 |
| Gitleaks 工作树快照 | `git ls-files` 返回的 167 个现存普通文件，使用当时工作树内容 | 未通过：1 项，退出码 1 |
| Ruff 代码检查 | `backend/`，不自动修复 | 未通过：16 项，退出码 1 |
| Ruff 格式检查 | `backend/`，只检查 | 未通过：13 个文件需格式化，75 个文件已符合格式，退出码 1 |
| Pyright | `backend/src`，显式使用 `backend/.venv/bin/python` | 未通过：54 个文件，7 个错误、0 个警告，退出码 1 |
| 前端 ESLint | `frontend/` 的 `pnpm lint` | 未完成代码检查：缺少 ESLint 配置，退出码 2 |
| 前端生产构建 | 已存在 `frontend/dist/index.html` | 本次未重新构建，不能据此判定当前源码构建通过 |

脱敏机器可读结果见 [scan-summary.json](./scan-summary.json)。暂存区通过只说明当时的已暂存差异没有命中规则，不代表整个仓库通过。

本次新增交付内容另做 Gitleaks 脱敏扫描：3 份 README、演示说明/脚本/清单与 9 个图片/GIF，共 15 个文件，0 项发现、退出码 0。此结果仅针对这些交付文件；图片扫描不包含 OCR，不能抵消上表的既有仓库发现。安全说明与汇总 JSON 也单独扫描，0 项发现。

## 凭据扫描发现

历史扫描与工作树快照均报告以下位置：

| 文件 | 行号 | 规则 | 历史提交 |
| --- | --- | --- | --- |
| `deploy/milvus/user.yaml` | 3 | `generic-api-key` | `44465d8ecf7306de2625c99a6c3898cbfc2944fc` |

这是同一文件位置在两种扫描范围中的发现，不应将其表述为两个独立凭据。报告没有包含凭据内容、匹配片段或作者信息；没有测试该值是否仍然有效。

处理建议：由凭据所有者确认来源，并在服务方撤销或轮换潜在暴露的凭据；后续使用本地或部署环境中的秘密配置。仅删除当前文件中的值不能消除既有 Git 历史记录。不要通过新增白名单来压制真实发现，处理后应重新扫描当前文件与历史。

## 版本与范围

- Gitleaks `8.30.1`，使用根目录 `.gitleaks.toml`，全程 `--redact=100`。
- Ruff `0.17.5`；Pyright `1.1.414`；Node.js `v22.23.4`；pnpm `12.21.0`；ESLint `9.39.5`。
- 检查时 HEAD 为 `9f642ef301971d5979376ab6cd068b5fb0f08155`，工作树另有未提交改动；结果是检查时的快照。
- 工作树快照复制了 `git ls-files` 返回的全部 167 个现存普通文件，共 15,066,551 字节，无缺失文件或符号链接。未包含未跟踪文件、被忽略文件、`.env`、依赖目录及本次新生成的报告。
- Gitleaks 仍按配置与自身文件处理规则扫描；导出文件总大小不等于实际分析文本字节数。配置继承默认规则，增加 AI API Key 规则，并排除依赖锁文件；`.gitleaksignore` 为空。
- 原始报告与工具日志仅放在临时目录，未加入项目交付。公开 JSON 只保留状态、计数、规则、文件位置和必要版本信息。

## 静态检查详情

Ruff 共报告 16 项：`I001` 7 项、`F401` 7 项、`B007` 1 项、`UP035` 1 项。涉及导入顺序、未使用导入、未使用的循环变量和类型导入更新。

Pyright 在显式选择项目虚拟环境后报告 `reportArgumentType` 4 项、`reportAttributeAccessIssue` 3 项。文件包括 `agents/chitchat/chitchat.py`、`agents/claim/tools.py`、`agents/orchestrator.py`、`infra/checkpointer.py`。其中理赔工具将 TypedDict 上下文当作对象属性访问。初次直接调用 Pyright 未绑定项目解释器时出现 118 个导入错误和 1 个警告；显式选择虚拟环境后的结果才用于上表，未通过改代码消除诊断。

前端 `pnpm lint` 调用了 ESLint 9，因找不到 `eslint.config.js`、`eslint.config.mjs` 或 `eslint.config.cjs` 而退出，不能解释为代码没有问题。本次按要求保留已有构建，不重新写入 `frontend/dist`。

## 复查命令

在仓库根目录运行现有任务：

```bash
task security:scan
task security:scan:all
task security:scan:dir
```

第三条会扫描真实目录，其范围比本次导出的受 Git 跟踪文件快照更广，不应将两者混同。

后端只读检查可在 `backend/` 执行：

```bash
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check --no-cache .
.venv/bin/pyright --pythonpath .venv/bin/python
```

前端在 `frontend/` 执行 `pnpm lint`。`pnpm build` 会生成或更新构建产物，本次未执行。

本记录不等于漏洞评估或部署验收；扫描范围、规则未覆盖的内容以及运行时行为均不由上述通过状态证明。
