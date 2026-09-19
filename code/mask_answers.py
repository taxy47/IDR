import io
import cv2
import numpy as np
from PIL import Image
import pymupdf

def process_page_all_options(img_bgr):
    """
    精准检测图像中所有选项（方框/圆形，灰色/绿色），并统一覆盖为纯灰色框
    """
    # 1. 转为灰度图
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 2. 图像二值化/边缘检测（提取所有图标的几何轮廓）
    # 使用 Canny 边缘检测，不论框是什么颜色，只要有边界线就能抓出来
    edges = cv2.Canny(gray, 50, 150)

    # 3. 膨胀边缘，把断开的线条连起来
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    # 4. 寻找所有闭合轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    detected_boxes = []

    for cnt in contours:
        # 获取轮廓的外接矩形
        x, y, w, h = cv2.boundingRect(cnt)
        
        # -------------------------------------------------------------
        # 筛选条件（根据选项框的几何特征过滤无关几何图形）：
        # 1. 面积在合理区间（避免抓到微小噪点或巨大的整页边框）
        # 2. 宽高比接近 1:1（无论方框还是圆，外接矩形都是接近正方形）
        # -------------------------------------------------------------
        area = w * h
        aspect_ratio = float(w) / h

        # 这里的 500~10000 适合 dpi=200 下的选项框大小，宽高比限制在 0.7~1.3 之间
        if 500 < area < 12000 and 0.7 <= aspect_ratio <= 1.3:
            # 排除重复嵌套的轮廓（比如框的内壁和外壁）
            is_duplicate = False
            for bx, by, bw, bh in detected_boxes:
                if abs(x - bx) < 15 and abs(y - by) < 15:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                detected_boxes.append((x, y, w, h))

    # 5. 在所有识别出的选项位置，统一覆盖为标准的纯灰色实心矩形 (BGR: 128, 128, 128)
    for x, y, w, h in detected_boxes:
        # 微调边缘，稍微扩大 2 像素完全盖住边缘
        cv2.rectangle(img_bgr, (x - 2, y - 2), (x + w + 2, y + h + 2), (128, 128, 128), -1)

    return len(detected_boxes)

def mask_all_options_pdf(input_pdf_path, output_pdf_path):
    doc = pymupdf.open(input_pdf_path)
    new_doc = pymupdf.open()

    print(f"正在扫描并处理 PDF 中的所有选项框，共 {len(doc)} 页...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 渲染高分辨率图像
        pix = page.get_pixmap(dpi=200)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        if pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = img_np.copy()

        # 精准处理所有选项
        count = process_page_all_options(img_bgr)

        # 转回 RGB 准备保存
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG', quality=95)
        
        # 写回 PDF 页面
        page_doc = pymupdf.open("jpeg", img_byte_arr.getvalue())
        pdf_bytes = page_doc.convert_to_pdf()
        img_pdf = pymupdf.open("pdf", pdf_bytes)

        new_doc.insert_pdf(img_pdf)
        print(f"第 {page_num + 1}/{len(doc)} 页处理完成，共重置覆盖了 {count} 个选项图标。")

    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()
    print(f"\n全部处理成功！刷题版 PDF 已保存至: {output_pdf_path}")

if __name__ == "__main__":
    input_file = "电磁场_带答案80页.pdf"      # 你的源 PDF 文件
    output_file = "电磁场_全覆盖刷题版.pdf"    # 输出文件

    mask_all_options_pdf(input_file, output_file)
