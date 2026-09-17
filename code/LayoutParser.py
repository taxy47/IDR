import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

import pymupdf
from PIL import Image
from paddleocr import PPStructureV3

doc = pymupdf.open("../materials/sample.pdf")
engine = PPStructureV3(lang="ch")

for page_idx, page in enumerate(doc):
    # 1. 导出图像
    pix = page.get_pixmap(dpi=150)
    img_path = f"temp_page_{page_idx}.png"
    pix.save(img_path)

    # 2. 强制将长边限制在 1200 像素以内，防止内存爆炸
    img = Image.open(img_path)
    max_side = 1200
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(img_path)

    # 3. 安全推理
    output = engine.predict(img_path)

    for res in output:
        print(res.json)
        res_dict = res.json 
        regions = res_dict.get("parsing_res_list", [])
        for region in regions:
            print(f"区块类型: {region.get('type')}, 边界框: {region.get('bbox')}")
