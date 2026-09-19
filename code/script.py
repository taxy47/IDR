import fitz  # 即 PyMuPDF

def extract_pages_by_keywords(input_pdf, output_pdf, keywords):
    # 打开源 PDF
    doc = fitz.open(input_pdf)
    matched_page_numbers = []

    print(f"正在扫描 PDF，共 {len(doc)} 页...")

    # 遍历所有页面
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 提取当前页面的所有文本
        text = page.get_text()

        # 检查是否包含关键词中的任意一个
        if any(keyword in text for keyword in keywords):
            matched_page_numbers.append(page_num)
            print(f"-> 在第 {page_num + 1} 页找到了目标字段！")

    if not matched_page_numbers:
        print("未找到包含目标字段的页面。")
        return

    # 创建新的 PDF 对象并插入符合条件的页面
    new_doc = fitz.open()
    for page_num in matched_page_numbers:
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    # 保存导出
    new_doc.save(output_pdf)
    new_doc.close()
    doc.close()
    print(f"\n提取完成！共提取 {len(matched_page_numbers)} 页，已保存至: {output_pdf}")

# --- 使用示例 ---
input_file = "your_paper.pdf"      # 替换为你的输入文件路径
output_file = "extracted_questions.pdf" # 导出文件路径
target_keywords = ["单选题", "多选题", "单项选择题", "多项选择题"] # 自定义需要匹配的关键词

extract_pages_by_keywords(input_file, output_file, target_keywords)
