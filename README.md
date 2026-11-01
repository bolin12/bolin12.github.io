# 个人主页(GitHub Pages)

- 改简历:只改 `_data/resume.yml`。推送后网页简历自动更新,CI 同时重新生成 `resume/main.tex`(不含手机号)。
- 需要 PDF:把 `resume/` 里的 `main.tex` 和 `resume.cls` 放进 Overleaf(或运行 `scripts/zip-resume.ps1` 生成 `resume.zip` 上传),用 XeLaTeX 编译;手机号在 Overleaf 里手动加到 `\ResumeContacts{...}`,不要写进仓库。
- 其他页面各改各的文件:首页 `index.md`、姓名与定位 `_config.yml`、关于 `about.md`、项目卡片 `_data/projects.yml`、项目详情 `projects/`、博客 `_posts/`。
