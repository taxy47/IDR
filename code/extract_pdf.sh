# 1. 创建临时文件夹
mkdir -p /tmp/pdf_pages

# 2. 将需要的页面提取为单页文件
for p in $(pdfgrep -n -e "单选题" -e "多选题" input.pdf | cut -d: -f1 | sort -u -n); do
    pdfseparate -f $p -l $p input.pdf /tmp/pdf_pages/page_%04d.pdf
done

# 3. 合并所有提取的页面并清理临时文件
pdfunite /tmp/pdf_pages/page_*.pdf output.pdf && rm -rf /tmp/pdf_pages
