# 安心保前端

使用 React 18、TypeScript、Vite 6 和 Ant Design 5 构建的保险商城与智能顾问界面。

完整项目说明、真实功能 GIF、Agent 流程图和安全扫描记录见[项目 README](../README.md)。

## 功能

- 商城：保险分类筛选、产品卡片、产品详情。
- 智能顾问：SSE 对话、条款引用抽屉、推荐方案确认与取消。
- 会话：新建、重命名、切换历史与删除。
- 理赔：材料及流程指引展示；查询功能的当前后端限制见主 README。
- 教学投保页：已有分步 UI，部分依赖的业务 API 尚未在当前后端注册。

## 开发

在仓库根目录执行 `pnpm install`，然后在本目录执行：

```bash
cp -n .env.example .env.local
pnpm dev
```

默认访问 <http://localhost:5173>。Vite 将 `/api` 代理到 `http://127.0.0.1:8001`；可在 `.env.local` 中设置 `VITE_BACKEND_HOST` 和 `VITE_BACKEND_PORT`。

也可在仓库根目录运行 `task fe:dev`。当前 `deploy/docker-compose.yml` 只包含基础组件，没有可供 `docker compose up frontend` 启动的前端服务。

## 演示

![安心保全项目功能演示](../backend/docs/assets/project-demo.gif)

当前登录表单使用固定本地教学用户，不调用真实登录接口，也没有 JWT 认证；产品、会话与聊天功能调用真实后端。GIF 录制及重录方法见[演示说明](../backend/docs/demo/README.md)。

## 检查与构建

```bash
pnpm lint
pnpm build
```

2026-11-18 检查中，ESLint 因缺少 `eslint.config.*` 配置未完成；本次未重新构建前端，已有 `dist/` 不代表当前源码构建通过。详细结果见[检查记录](../backend/docs/security/SCAN-RESULTS.md)。
