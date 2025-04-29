import os
from app import logger
from docx import Document
import pdfplumber

TEMPLATE_OBJECTIVE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'template', 'objective')


def read_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

    elif ext == '.pdf':
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
            text = '\n'.join(page for page in pages if page)

    elif ext == '.docx':
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = '\n'.join(paragraphs)

    else:
        logger.warning(f"Unsupported file format: {file_path}")

    return text


def load_template_answers_from_file(file_path):
    """
    从模板文件加载答案，返回一个字典，格式为 {题目编号: 答案}
    """
    answers = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            # 读取题目编号（当前行），并去掉小数点
            question_line = lines[i].strip()
            question_number = question_line.split('.')[0]  # 去掉小数点

            # 读取答案行（下一行）
            if i + 1 < len(lines):
                answer_line = lines[i + 1].strip()

                # 确保答案行以“答案：”开头
                if answer_line.startswith("答案："):
                    # 提取答案部分
                    answer = answer_line.split('答案：')[1].strip()
                    answers[question_number] = answer
                    logger.info("Question: %s, Answer: %s", question_number, answer)


            # 移动到下一题（跳过当前题号行和答案行）
            i += 2

    return answers

def load_all_objective_templates():
    """
    加载目录下所有模板文件的答案
    """
    template_objective_answers = {}
    for filename in os.listdir(TEMPLATE_OBJECTIVE_DIRECTORY):
        if filename.endswith(".txt"):
            file_path = os.path.join(TEMPLATE_OBJECTIVE_DIRECTORY, filename)
            template_objective_answers[filename] = load_template_answers_from_file(file_path)

    return template_objective_answers

def objective_grade_submission(submitted_answers, template_name, template_objective_answers):
    """
    根据用户提交的答案与模板答案进行对比评分
    """
    template = template_objective_answers.get(template_name)
    if not template:
        return 0, 0  # 如果没有找到对应的模板文件

    score = 0
    total_questions = len(template)

    for question_number, answer in submitted_answers.items():
        # 如果用户答案与模板答案匹配，则加分
        if template.get(question_number) == answer:
            score += 10

    return score, total_questions