---
search: false
---

# FurinaChronicle 文档站维护

此目录为 VitePress 源码。公开地址采用 `/furinachronicle/`。仓库的 GitHub Pages 从 `main` 分支的 `docs/` 发布，VitePress 只构建 `docs/furinachronicle/` 子目录。

从仓库根目录运行以下命令。建议使用 Node.js 22。

```powershell
cd sites/furinachronicle
npm ci
npm run build
npm run preview
```

预览入口为 `http://localhost:4173/furinachronicle/`。日常编辑可以运行 `npm run dev`。每次更新文档后重新构建，检查生成文件及旧资源清理情况，并将源码、依赖锁和生成文件一并纳入 Pages 的发布变更。对外使用协议和隐私政策应替换对应固定路径的预留页，生效文件另按版本存档。
