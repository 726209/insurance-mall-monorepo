# 功能演示与复录

本目录保存 README 的真实功能演示录制脚本和清单。GIF 位于 [`../assets/`](../assets/)，录制状态见 [`demo-manifest.json`](./demo-manifest.json)。录制运行真实前端、后端与模型/RAG；没有伪造产品、模型回复或工具返回值。

## 演示内容

| 文件 | 内容 |
| --- | --- |
| `project-demo.gif` | 按顺序合成的全项目功能演示，约 82 秒 |
| `01-product-catalog.gif` | 产品分类、产品详情 |
| `02-clause-citations.gif` | 条款问答、可点击引用、条款抽屉 |
| `03-plan-confirmation.gif` | 推荐方案、确认卡、确认后继续执行 |
| `04-claim-guidance.gif` | 医疗险理赔材料与流程指引 |
| `05-thread-management.gif` | 新建、重命名、历史切换、删除本次创建的空会话 |

截图为 1440 × 960，GIF 为 1200 × 800、每秒 2 帧、循环播放。相同画面的连续等待会被压缩；字幕是录制脚本添加的说明层，不是应用的新功能。原始截图序列保留在运行时临时目录，未加入仓库。

## 录制前准备

1. 按[项目说明](../../../README.md)启动前端、后端及依赖，默认前端地址为 `http://localhost:5173`。
2. 使用教学环境，确认 `user_id=1` 为演示用户；产品与条款知识库已导入。
3. 准备 Node.js、Google Chrome、FFmpeg，以及 `playwright-core`。脚本不下载浏览器。
4. 录制会创建演示会话，并在方案片段中确认保存一份“演示·意外保障方案”；会话管理片段只删除本次创建的空会话。不要在真实客户环境运行。

在仓库根目录执行，录制依赖安装到临时目录，不修改项目依赖：

```bash
npm install --prefix /tmp/hm-insurance-demo-tools \
  --no-audit --no-fund --ignore-scripts playwright-core

HM_DEMO_PLAYWRIGHT_MODULE=/tmp/hm-insurance-demo-tools/node_modules/playwright-core/index.mjs \
HM_DEMO_DEMO_SESSION=1 \
node backend/docs/demo/record-demo.mjs
```

`HM_DEMO_DEMO_SESSION=1` 载入项目自带的本地教学用户会话，与前端教学登录使用相同的用户 ID；它不是认证绕过能力或后端登录接口。省略时，脚本会操作页面登录按钮。

## 可选配置

| 环境变量 | 默认值 / 用途 |
| --- | --- |
| `HM_DEMO_PLAYWRIGHT_MODULE` | `playwright-core`；支持模块入口的绝对路径 |
| `HM_DEMO_BASE_URL` | `http://localhost:5173` |
| `HM_DEMO_CHROME` | macOS Google Chrome 可执行文件路径；其他系统需自行指定 |
| `HM_DEMO_SECTIONS` | `catalog,advisor,plan,claims,threads`；可选择部分重录 |
| `HM_DEMO_DEMO_SESSION` | `1` 表示使用固定教学用户会话 |

例如仅重录条款引用：

```bash
HM_DEMO_PLAYWRIGHT_MODULE=/tmp/hm-insurance-demo-tools/node_modules/playwright-core/index.mjs \
HM_DEMO_DEMO_SESSION=1 HM_DEMO_SECTIONS=advisor \
node backend/docs/demo/record-demo.mjs
```

脚本通过独立浏览器上下文录制，仅保留本次或清单中此前录制创建的会话列表。产品、聊天、条款与方案接口仍来自实际服务。旧会话不会被删除，脚本也不读取用户现有浏览器会话。

模型回复具有不确定性。脚本将未完成片段标记为 `partial`，需要检查运行日志和画面后再将其作为成功演示发布。清单不包含 API Key、密码或完整聊天正文。
