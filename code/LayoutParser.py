import pymupdf
from paddleocr import PPStructureV3

# 1. 将 PDF 页面转换为图像
doc = pymupdf.open("../materials/sample.pdf")
engine = PPStructureV3(show_log=False, lang="ch")

for page_idx, page in enumerate(doc):
  pix = page.get_pixmap(dpi=150)
  img_path = f"temp_page_{page_idx}.png"
  pix.save(img_path)

  # 2. 执行版面分析与识别
  result = engine(img_path)

  # 3. 遍历切分出的各个版面区块
  for region in result:
    region_type = region["type"]  # 区域类型：text, title, table, figure 等
    bbox = region["bbox"]  # 坐标：[x1, y1, x2, y2]
    content = region.get("res", [])  # 对应区域的文本或结构化数据
    print(f"区块类型: {region_type}, 边界框: {bbox}")
