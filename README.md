# 个人主页(私有源码 + 公开成品)

这个仓库是**私有**的,里面有批注、待补清单、草稿和 LaTeX。公开的只有构建好的网站,由 Actions 推到公开仓库 `bolin12/bolin12.github.io`。

## 日常
- 改简历:只改 `_data/resume.yml`(中文)。英文版 `_data/resume_en.yml` 在你改完中文后让 Claude 补齐。
- 批注与待补:源码里的 `# TODO(补充)`、`note:` 字段和项目页里的 `{% comment %}` 块,**公开站点永远不会显示**。
  所有待补项汇总在 `NOTES.md`(自动生成)。
- 想看带批注的完整页面:到 Actions 里最近一次 "Build and publish the site",下载产物 `site-preview-with-notes`,解压后用本地服务器打开。
- 推送后 Actions 会:构建公开版 → 安全检查(发现批注、草稿、手机号、源码文件就让构建失败)→ 推送到公开仓库。

## 要 PDF
把 `resume/` 里的 `main.tex` 和 `resume.cls`(英文版只要 `main_en.tex`)放进 Overleaf 编译;手机号在 Overleaf 里自己加,不要写进仓库。

## 前置设置(只需一次)
私有仓库的 Settings → Secrets and variables → Actions 里添加 `PUBLIC_REPO_TOKEN`:一个只对公开仓库有 Contents 读写权限的 fine-grained token。未设置时只构建和检查,不发布。
