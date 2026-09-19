from pathlib import Path
import sys

import pymupdf
import genanki


# ============================================================
# 配置
# ============================================================

# PDF 渲染分辨率
# 150：文件较小，通常够用
# 200：比较推荐
# 300：文字/公式更清晰，但文件会明显变大
DPI = 200


# ============================================================
# PDF → PNG
# ============================================================

def pdf_to_images(pdf_path: Path, output_dir: Path, prefix: str):
    """
    将 PDF 每一页渲染为 PNG。

    返回：
        list[Path]
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n打开 PDF：{pdf_path}")

    # 新版 PyMuPDF API
    document = pymupdf.open(pdf_path)

    image_paths = []

    # 72 DPI 是 PDF 的默认基准
    scale = DPI / 72

    matrix = pymupdf.Matrix(scale, scale)

    total_pages = len(document)

    for page_number in range(total_pages):

        page = document[page_number]

        # 渲染页面
        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_path = (
            output_dir /
            f"{prefix}_{page_number + 1:04d}.png"
        )

        pixmap.save(image_path)

        image_paths.append(image_path)

        print(
            f"  [{page_number + 1:>4}/{total_pages}] "
            f"{image_path.name}"
        )

    document.close()

    return image_paths


# ============================================================
# 创建 Anki
# ============================================================

def create_anki(
    question_images,
    answer_images,
    output_file: Path
):
    """
    创建 Anki .apkg。

    question_images[i]
        ↓
    Front

    answer_images[i]
        ↓
    Back
    """

    # --------------------------------------------------------
    # 检查页数
    # --------------------------------------------------------

    if len(question_images) != len(answer_images):

        raise ValueError(
            "\n"
            "习题 PDF 和答案 PDF 页数不一致！\n"
            f"习题：{len(question_images)} 页\n"
            f"答案：{len(answer_images)} 页\n"
            "\n"
            "当前脚本要求两个 PDF 按页一一对应。"
        )

    # --------------------------------------------------------
    # 创建 Anki Note 类型
    # --------------------------------------------------------

    model = genanki.Model(
        model_id=1607392319,

        name="PDF Exercise",

        fields=[
            {
                "name": "Question"
            },
            {
                "name": "Answer"
            }
        ],

        templates=[
            {
                "name": "Card",

                # 正面
                "qfmt": """
                    <div class="page">
                        {{Question}}
                    </div>
                """,

                # 背面
                "afmt": """
                    <div class="page">
                        {{FrontSide}}
                    </div>

                    <hr id="answer">

                    <div class="page">
                        {{Answer}}
                    </div>
                """
            }
        ],

        css="""
            .card {
                font-family: Arial, sans-serif;
                font-size: 20px;
                text-align: center;
                background-color: white;
                color: black;
            }

            .page {
                width: 100%;
                height: 100%;
            }

            .page img {
                max-width: 100%;
                max-height: 90vh;
                object-fit: contain;
            }

            hr#answer {
                margin: 20px 0;
            }
        """
    )

    # --------------------------------------------------------
    # 创建牌组
    # --------------------------------------------------------

    deck = genanki.Deck(
        deck_id=2059400110,
        name="PDF习题"
    )

    # --------------------------------------------------------
    # 创建 Package
    # --------------------------------------------------------

    package = genanki.Package(deck)

    # --------------------------------------------------------
    # 创建卡片
    # --------------------------------------------------------

    for index, (question, answer) in enumerate(
        zip(question_images, answer_images),
        start=1
    ):

        question_filename = question.name
        answer_filename = answer.name

        note = genanki.Note(
            model=model,

            fields=[
                f'<img src="{question_filename}">',
                f'<img src="{answer_filename}">'
            ]
        )

        deck.add_note(note)

        # 把图片加入 Anki 媒体文件
        package.media_files.append(
            str(question)
        )

        package.media_files.append(
            str(answer)
        )

        print(
            f"  创建卡片："
            f"[{index:>4}/{len(question_images)}]"
        )

    # --------------------------------------------------------
    # 写入 .apkg
    # --------------------------------------------------------

    package.write_to_file(output_file)


# ============================================================
# 主程序
# ============================================================

def main():

    # --------------------------------------------------------
    # 参数检查
    # --------------------------------------------------------

    if len(sys.argv) != 3:

        print(
            "\n"
            "用法：\n"
            "\n"
            "python pdf_to_anki.py 习题.pdf 答案.pdf\n"
        )

        sys.exit(1)

    question_pdf = Path(sys.argv[1])
    answer_pdf = Path(sys.argv[2])

    # --------------------------------------------------------
    # 检查文件
    # --------------------------------------------------------

    if not question_pdf.exists():

        print(
            f"错误：找不到习题 PDF："
            f"{question_pdf}"
        )

        sys.exit(1)

    if not answer_pdf.exists():

        print(
            f"错误：找不到答案 PDF："
            f"{answer_pdf}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # 输出目录
    # --------------------------------------------------------

    output_dir = Path(
        "pdf_to_anki_output"
    )

    image_dir = (
        output_dir /
        "images"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 1. 处理习题 PDF
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("1. 转换习题 PDF")
    print("=" * 60)

    question_images = pdf_to_images(
        question_pdf,
        image_dir,
        "question"
    )

    # --------------------------------------------------------
    # 2. 处理答案 PDF
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("2. 转换答案 PDF")
    print("=" * 60)

    answer_images = pdf_to_images(
        answer_pdf,
        image_dir,
        "answer"
    )

    # --------------------------------------------------------
    # 3. 检查页数
    # --------------------------------------------------------

    if len(question_images) != len(answer_images):

        print("\n")
        print("=" * 60)
        print("错误：PDF 页数不一致")
        print("=" * 60)

        print(
            f"习题 PDF：{len(question_images)} 页"
        )

        print(
            f"答案 PDF：{len(answer_images)} 页"
        )

        print(
            "\n当前脚本要求：\n"
            "习题第 N 页 ↔ 答案第 N 页"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # 4. 创建 Anki
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("3. 创建 Anki")
    print("=" * 60)

    output_file = (
        output_dir /
        f"{question_pdf.stem}_Anki.apkg"
    )

    create_anki(
        question_images,
        answer_images,
        output_file
    )

    # --------------------------------------------------------
    # 完成
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("完成！")
    print("=" * 60)

    print(
        f"\nAnki 文件：\n"
        f"{output_file}"
    )

    print(
        f"\n卡片数量："
        f"{len(question_images)}"
    )

    print(
        "\n导入方法：\n"
        "直接双击 .apkg 文件，"
        "或者在 Anki 中选择导入。"
    )


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    main()
