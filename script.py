import os
import sys
import pymupdf
#import paddleocr 
#import pa
from paddleocr import PaddleOCR

ocr = PaddleOCR(
	use_doc_orientation_classify=False,
	use_doc_unwarping=False,
	use_textline_orientation=False,
	enable_mkldnn=False,
	engine="paddle",
)
result = ocr.predict("./pic/IMG_20260830_234003.jpg")
for res in result:
	res.print()
	res.save_to_img("output")
	res.save_to_json("output")

#	add a commit

## print(dir(os))
#print("Hello, Arch Linux")
#print("Hello, Arch Linux")

# doc = pymupdf.open("./materials/sample.pdf")
#doc = pymupdf.open("./script.txt")
#print(doc)
##
#out = open("output.txt", "wb")
#for page in doc:
#	text = page.get_text().encode("utf8")
#	out.write(text)
#	out.write(bytes((12,)))
#out.close()
#doc.close()
