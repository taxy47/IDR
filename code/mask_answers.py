import io
import cv2
import numpy as np
from PIL import Image
import pymupdf  # PyMuPDF 新版推荐写法

def auto_clean_quiz_pdf(input_pdf_path, output_pdf_path):
    # 打开源 PDF 并创建新 PDF
    doc = pymupdf.open(input_pdf_path)
    new_doc = pymupdf.open()

    print(f"正在处理 PDF，共 {len(doc)} 页...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 将 PDF 页面渲染为高分辨率图像 (dpi=200 保证公式清晰)
        pix = page.get_pixmap(dpi=200)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        # 转换为 OpenCV 处理需要的 BGR 格式
        if pix.n == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = img_np.copy()

        # 转换为 HSV 颜色空间以定位绿色答案图标
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # 绿色的 HSV 范围
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])

        # 生成掩膜并提取轮廓
        mask = cv2.inRange(hsv, lower_green, upper_green)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        has_masked = False
        img_height, img_width = img_bgr.shape[:2]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # 过滤小噪点，只捕捉有效的选项绿框
            if area > 100:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # -------------------------------------------------------------
                # 核心改进逻辑：
                # 找到绿框的横坐标 X，直接用纯白色 (255, 255, 255) 把左侧这一整列 
                # (从顶部 y=0 到底部 y=img_height) 的 ABCD 方块全抹平！
                # -------------------------------------------------------------
                padding_x = 15  # 横向左右扩展的宽度，确保把边界完全覆盖
                left_x = max(0, x - padding_x)
                right_x = min(img_width, x + w + padding_x)
                
                # 将整列涂白
                cv2.rectangle(img_bgr, (left_x, 0), (right_x, img_height), (255, 255, 255), -1)
                
                has_masked = True
                break  # 抹掉整列后直接跳出，处理下一页

        # 将处理后的 BGR 图像转换回 RGB 格式
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 将内存图片转回 PDF 格式页面
        pil_img = Image.fromarray(img_rgb)
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG', quality=95)
        
        # 通过字节流重新打包进 PyMuPDF 页面
        page_doc = pymupdf.open("jpeg", img_byte_arr.getvalue())
        pdf_bytes = page_doc.convert_to_pdf()
        img_pdf = pymupdf.open("pdf", pdf_bytes)

        # 追加到新 PDF 文档中
        new_doc.insert_pdf(img_pdf)
        
        status = "已擦除选项图标列" if has_masked else "无绿色答案，保持原样"
        print(f"第 {page_num + 1}/{len(doc)} 页处理完成 ({status})")

    # 保存最终 PDF
    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()
    print(f"\n处理成功！处理后的刷题版 PDF 已保存至: {output_pdf_path}")

# --- 运行参数设置 ---
if __name__ == "__main__":
    input_file = "电磁场_带答案80页.pdf"      # 替换为你的源 PDF 路径
    output_file = "电磁场_刷题版_无提示.pdf"  # 导出的目标 PDF 路径

    auto_clean_quiz_pdf(input_file, output_file)
