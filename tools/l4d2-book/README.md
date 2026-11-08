# 求生之路 2 地图制作网页版

读本由 InDesign 导出的带结构标签 PDF 生成。当前底本为 2026 年 6 月 14 日导出的第一版 v0.8.1（文件名以 v0.8.1)-2.pdf 结尾）。页面和站内搜索均为静态文件，部署在 GitHub Pages 的 docs/l4d2-book/。

第 1 至 10 章使用完整的原书章节页作封面。封面导语保留在网页文字和搜索索引中。

图 1-4-1 按原页上的完整图示范围渲染，包含截图右侧的 InDesign 引线和编号。换版时核对该图的裁剪范围。

## 从 PDF 重新构建

在仓库根目录运行以下 PowerShell 命令。将 $pdf 设为本地 PDF 的完整路径。Python 需要 3.11 或以上。

~~~powershell
$tool = 'tools/l4d2-book'
$cache = Join-Path ([IO.Path]::GetTempPath()) ('l4d2-book-' + [guid]::NewGuid())
python -m pip install PyMuPDF pdfplumber Pillow lxml
python "$tool/extract.py" $pdf "$cache/book.json" "$cache/figures"
python "$tool/build.py" "$cache/book.json" 'docs/l4d2-book' --assets "$cache/figures"
python "$tool/verify.py" 'docs/l4d2-book'
~~~

换版时核对 build.py 中的版次说明、原书页码偏移和章节导航。确认脚本报告所有书签都能链接到对应标题，再抽查带图的步骤、跨页表格和附录配置代码。发布只需提交 docs/l4d2-book/ 下的生成文件和转换脚本。PDF 与中间文件留在本地。
