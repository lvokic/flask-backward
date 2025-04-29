from flask import request, jsonify, make_response
from app.template_loader import load_all_objective_templates, objective_grade_submission
from app import handle_file_upload
import docx
import pdfplumber
import logging

TEMPLATE_OBJECTIVE_FOLDER = "app/template/objective"
TEMPLATE_SUBJECTIVE_FOLDER = "app/template/subjective"

PROBLEM_OBJECTIVE_FOLDER = "app/problems/objective"
PROBLEM_SUBJECTIVE_FOLDER = "app/problems/subjective"
PROBLEM_OPEN_FOLDER = "app/problems/open"  # 半主观题文件上传目录

# 在应用启动时加载所有模板文件
template_objective_answers = load_all_objective_templates()


# ----------------------------------  -模版上传模块- -------------------------------------#
def handle_template_objective_file_upload():
    """
    处理客观题模板文件上传并保存到服务器
    """
    return handle_file_upload(TEMPLATE_OBJECTIVE_FOLDER)


def handle_template_subjective_file_upload():
    """
    处理主观题模板文件上传并保存到服务器
    """
    return handle_file_upload(TEMPLATE_SUBJECTIVE_FOLDER)
# ----------------------------------  -模版上传模块- -------------------------------------#



# ----------------------------------  -问题上传模块- -------------------------------------#
def handle_problem_objective_file_upload():
    """
    处理客观题文件上传并保存到服务器
    """
    return handle_file_upload(PROBLEM_OBJECTIVE_FOLDER)


def handle_problem_subjective_file_upload():
    """
    处理半开放文件上传并保存到服务器
    """
    return handle_file_upload(PROBLEM_SUBJECTIVE_FOLDER)


def handle_problem_open_file_upload():
    """
    处理主观题文件上传并保存到服务器
    """
    return handle_file_upload(PROBLEM_OPEN_FOLDER)
# ----------------------------------  -问题上传模块- -------------------------------------#


def read_text_from_file(file):
    filename = file.filename.lower()
    if filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif filename.endswith('.docx'):
        doc = docx.Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    elif filename.endswith('.pdf'):
        pdf_text = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                pdf_text.append(page.extract_text() or '')
        return '\n'.join(pdf_text)
    else:
        raise ValueError("不支持的文件类型。仅支持txt、docx和pdf。")


def submit_homework_objective():
    """
    处理作业提交并评分
    """
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400

    # 获取表单数据
    student_id = request.form.get('studentId')  # 获取学生ID
    homework_id = request.form.get('homeworkID')  # 获取作业ID
    homework_name = request.form.get('homeworkName')  # 获取作业名称

    try:
        # 读取文件内容（自动根据文件类型识别）
        file_content = read_text_from_file(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    submitted_answers = {}
    file_lines = file_content.splitlines()  # 按行分割文件内容

    question_number = None  # 初始化题号
    answer = None  # 初始化答案

    for line in file_lines:
        # 查找题号和问题描述的行
        if line.strip().endswith("？"):  # 判断是否是题目行，通常题目以"？"结尾
            question_number = line.strip().split('.')[0]  # 提取题号，按"."分割
        # 查找答案行
        elif line.startswith("答案："):
            answer = line.split('答案：')[1].strip()  # 提取答案部分

            # 将题号和答案存入字典
            if question_number:
                submitted_answers[question_number] = answer
                # 打印日志信息
                logging.info("question: %s, answer: %s", question_number, answer)

    # 获取上传文件的名称（假设文件名与模板文件名相同）
    template_name = file.filename
    if template_name not in template_objective_answers:
        return jsonify({"error": "未找到对应的模板文件"}), 400

    # 比较用户答案与模板答案，计算得分
    score, total_questions = objective_grade_submission(submitted_answers, template_name, template_objective_answers)

    # 打印评分结果到日志
    logging.info("Score: %d, Total Questions: %d", score, total_questions)  # 打印评分结果

    # 创建响应对象
    response = make_response({
        "score": score,
        "completed": True,
        "category": "客观题",
        "studentId": student_id,
        "homeworkId": homework_id,
        "homeworkName": homework_name
    })

    # 设置响应的Content-Type为application/json
    response.headers['Content-Type'] = 'application/json'

    return response
