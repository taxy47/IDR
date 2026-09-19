import pymupdf  # 使用推荐的新版导入方式
import cv2
import numpy as np
import io
from PIL import Image

def mask_green_answers(input_pdf_path, output_pdf_path):
    # 打开源 PDF
    doc = pymupdf.open(input_pdf_path)
    new_doc = pymupdf.open()

    print(f"正在处理 PDF，共 {len(doc)} 页...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 将 PDF 页面渲染为高分辨率图像 (dpi=200 保证清晰度)
        pix = page.get_pixmap(dpi=200)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        # PyMuPDF 出来的格式是 RGB/RGBA，转换成 OpenCV 需要的 BGR
        if pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)

        # 转换为 HSV 颜色空间，精准提取“绿色”答案框
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # 定义绿色的 HSV 阈值范围（涵盖亮绿、草绿等）
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])

        # 创建绿色区域的掩膜
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 寻找图像中绿色的轮廓（即绿色方块）
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 遍历找到的绿色区域并覆盖为中灰色（BGR: 128, 128, 128）
        masked_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # 过滤掉微小的噪点，只处理有一定面积的选项方块
            if area > 100: 
                x, y, w, h = cv2.boundingRect(cnt)
                # 在绿色区域画一个灰色的实心矩形盖住它
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (128, 128, 128), -1)
                masked_count += 1

        # 将处理完的 BGR 图像转回 RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 将图像数据打包为 JPEG 格式字节流
        pil_img = Image.fromarray(img_rgb)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG', quality=95)
        
        # 修复关键点：通过 stream= 指定内存字节流，并声明 streamtype="pdf" 或直接加载图片转 PDF
        img_pdf = pymupdf.open("pdf", img_byte_arr.getvalue()) if hasattr(pymupdf, "open") else None
        
        # 使用 PyMuPDF 的 convert_to_pdf 更加稳健地处理单帧内存图片
        page_doc = pymupdf.open("jpeg", img_byte_arr.getvalue())
        pdf_bytes = page_doc.convert_to_pdf()
        img_pdf = pymupdf.open("pdf", pdf_bytes)

        # 将单页 PDF 插入到最终的 PDF 文档中
        new_doc.insert_pdf(img_pdf)
        
        print(f"第 {page_num + 1} 页处理完成，遮挡了 {masked_count} 处答案。")

    # 保存新的 PDF
    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()
    print(f"\n全部处理完成！无答案版 PDF 已保存至: {output_pdf_path}")

# --- 运行设置 ---
input_file = "电磁场_带答案80页.pdf"      # 请替换为你的真实输入 PDF 文件名
output_file = "电磁场_刷题版_无答案.pdf"  # 处理后的 PDF 保存路径

mask_green_answers(input_file, output_file)
