import io
import cv2
import numpy as np
from PIL import Image
import pymupdf

def process_page_safe(img_bgr):
    """
    只在页面左侧选项区域（X轴特定范围）进行图标检测与覆盖，彻底保护公式和文字
    """
    img_height, img_width = img_bgr.shape[:2]

    # 1. 转灰度图与边缘检测
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    detected_boxes = []

    # ----------------------------------------------------------------------
    # 区域限制设置：
    # 选项图标通常位于页面左侧 10% 到 30% 的区域内。
    # 我们设置 x_min 和 x_max，限制检测范围，防止误伤中间和右侧的公式！
    # ----------------------------------------------------------------------
    x_min_limit = int(img_width * 0.10)  # 左边界 (避开最左侧蓝条/边缘)
    x_max_limit = int(img_width * 0.30)  # 右边界 (在公式开始前截断)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 1. 空间位置限制：只处理位于 [x_min_limit, x_max_limit] 范围内的物体
        if not (x_min_limit <= x <= x_max_limit):
            continue

        # 2. 几何特征筛选
        area = w * h
        aspect_ratio = float(w) / h

        # 选项框的面积过滤（在 dpi=200 下，真正的选项框面积通常在 1500~8000 像素）
        if 1500 < area < 10000 and 0.7 <= aspect_ratio <= 1.3:
            # 排除重复嵌套的内轮廓
            is_duplicate = False
            for bx, by, bw, bh in detected_boxes:
                if abs(x - bx) < 20 and abs(y - by) < 20:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                detected_boxes.append((x, y, w, h))

    # 在安全筛选出的位置覆盖纯灰色矩形 (BGR: 128, 128, 128)
    for x, y, w, h in detected_boxes:
        cv2.rectangle(img_bgr, (x - 2, y - 2), (x + w + 2, y + h + 2), (128, 128, 128), -1)

    return len(detected_boxes)

def mask_options_safely_pdf(input_pdf_path, output_pdf_path):
    doc = pymupdf.open(input_pdf_path)
    new_doc = pymupdf.open()

    print(f"正在进行安全遮挡处理，共 {len(doc)} 页...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 渲染图像
        pix = page.get_pixmap(dpi=200)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        if pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = img_np.copy()

        # 安全处理选项，公式区域会被完全隔离
        count = process_page_safe(img_bgr)

        # 保存为图片字节流并打包为 PDF 页面
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG', quality=95)
        
        page_doc = pymupdf.open("jpeg", img_byte_arr.getvalue())
        pdf_bytes = page_doc.convert_to_pdf()
        img_pdf = pymupdf.open("pdf", pdf_bytes)

        new_doc.insert_pdf(img_pdf)
        print(f"第 {page_num + 1}/{len(doc)} 页处理完成，遮挡了 {count} 个选项图标。")

    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()
    print(f"\n处理完成！最终刷题版 PDF 已保存至: {output_pdf_path}")

if __name__ == "__main__":
    input_file = "电磁场_带答案80页.pdf"      # 你的源文件
    output_file = "电磁场_完美刷题版.pdf"    # 修正后的目标文件

    mask_options_safely_pdf(input_file, output_file)
