# 个人主页（GitHub Pages）

站点：https://bolin12.github.io 。这个仓库是**公开**的，GitHub 自己用 Jekyll 构建并发布，推送 `main` 就上线。

## 内容在哪
| 内容 | 位置 |
|---|---|
| 简历（中文，唯一内容来源） | `_data/resume.yml`；英文版 `_data/resume_en.yml`（改完中文后再补齐）；网页模板 `_includes/resume.html` |
| 项目页与子页 | `projects/`；子页用 front matter 的 `parent` 挂到项目下，目录侧栏自动生成（`order` 排序，`side_title` 是目录里的短名字） |
| 项目卡片（项目总览、首页） | `_data/projects.yml` |
| 个人页、首页 | `me.md`、`index.md`；姓名与定位在 `_config.yml` |
| 顶部导航 | `_data/nav.yml` |
| 草稿（线上排除，本地预览可见） | `drafts/` |
| LaTeX 简历 | `resume/`（`main.tex`、`main_en.tex` 由 CI 自动生成，不要手改） |

## 项目的进展与开发文档
**项目的进展和开发文档写在这里**（`projects/` 下的页面），不再放本地的 `Doc` 目录。还没准备好公开的先放 `drafts/`，本地预览能看到、线上看不到。站点是公开的，所以发布前要先过一遍：去掉本机路径、私有提交哈希、第三方或公司内部的资产与数据；状态要如实（规划就写规划，不写没做出来的结果）。

## 日常
- **本地预览（带批注和草稿）**：`powershell -File scripts\preview.ps1`，打开 http://localhost:4000 。需要装 Ruby，依赖在 `vendor/bundle`。同时会生成 `NOTES.md`（待补清单，已加入 `.gitignore`）。
- **批注与待补**：`_data/resume.yml` 里的 `# TODO(补充)`、`note:` 字段，以及项目页里的 `{% comment %}` 块，**网站上不会显示**（`show_notes: false`），但因为仓库是公开的，GitHub 上能读到源码。
- **推送前**：构建一遍，跑 `python scripts/check_public_output.py _site .`，并扫一遍全部历史里有没有手机号和明文邮箱。推送后 Actions 会做同样的构建与检查，只告警、不拦截发布。
- **写文件不要带 BOM**：Windows PowerShell 的 `Set-Content -Encoding utf8` 会加 BOM，Jekyll 因此会把源文件原样发布出去。
- 表格和列表前面要留一个空行，否则 Markdown 引擎不渲染。

## 要 PDF
把 `resume/` 里的 `main.tex` 和 `resume.cls`（英文版只要 `main_en.tex`）放进 Overleaf 编译。联系电话不放进仓库、网站和公开的 PDF，需要时在 Overleaf 里自己加。
