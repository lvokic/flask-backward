import os
import re
from app import get_model, save_student_homework
from flask import jsonify, make_response
from app import logger
import numpy as np

# 加载预训练的 Sentence-BERT 模型
model = get_model()

TEMPLATE_SUBJECTIVE_FOLDER = os.path.join(os.path.dirname(__file__), 'template', 'subjective')
PROBLEM_SUBJECTIVE_FOLDER = "app/uploads/subjective"
PROBLEM_OPEN_FOLDER = "app/uploads/open"

def convert_float32_to_float(value):
    """将 float32 转换为原生的 Python float 类型"""
    if isinstance(value, np.float32):  # 判断是否是 np.float32 类型
        return float(value)  # 转换为原生 Python float
    elif isinstance(value, dict):
        # 如果是字典，递归地转换字典中的值
        return {key: convert_float32_to_float(val) for key, val in value.items()}
    elif isinstance(value, list):
        # 如果是列表，递归地转换列表中的值
        return [convert_float32_to_float(val) for val in value]
    else:
        return value  # 如果是其他类型，返回原值


# 计算余弦相似度
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# 定义评分函数
def score_answer(student_answer, reference_answer):
    student_vector = model.encode(student_answer)
    reference_vector = model.encode(reference_answer)

    similarity = cosine_similarity(student_vector, reference_vector)

    current_score = similarity * 100
    current_score = min(max(current_score, 0), 100)
    current_score = convert_float32_to_float(current_score)
    return current_score


def get_reference_answer(file_name):
    file_path = os.path.join(TEMPLATE_SUBJECTIVE_FOLDER, f'{file_name}')

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None


def parse_answers(file_content):
    # 正则表达式：匹配每个问题的编号和其后面的答案内容
    pattern = r"(\d+)\.\s*(.*?)(?=\d+\.\s|$)"  # 匹配题号后面紧跟着的答案部分
    matches = re.findall(pattern, file_content, re.DOTALL)

    # 构建字典结构，问题编号作为key，答案作为value
    answers = {f"question {question}": answer.strip() for question, answer in matches}

    # 打印每个题目的答案到日志中
    for question, answer in answers.items():
        logger.info(f"{question}: {answer}")

    return answers


def score(file, student_id, homework_id, homework_name):
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    save_student_homework(file, student_id, homework_name, PROBLEM_SUBJECTIVE_FOLDER)

    results = {}

    if not hasattr(file, 'filename'):
        return jsonify({"error": "Invalid file uploaded"}), 400

    file_name = file.filename
    logger.info(f"Upload file: {file_name}")
    try:
        # 读取文件内容并解码
        student_file_content = file.read().decode('utf-8')
    except Exception as e:
        return jsonify({"error": f"Error reading file {file_name}: {str(e)}"}), 500

    # 解析学生提交的答案
    student_answers = parse_answers(student_file_content)

    # 获取参考答案
    reference_answer = get_reference_answer(file_name)

    if not reference_answer:
        results[file_name] = {"error": "Reference answer not found"}
    else:
        reference_answers = parse_answers(reference_answer)

        total_score = 0  # 总分数
        total_questions = len(student_answers)  # 总题目数

        # 对比参考答案与学生答案
        for question_number, student_answer in student_answers.items():
            if question_number not in reference_answers:
                results[file_name] = {"error": f"Reference answer for question {question_number} not found"}
            else:
                reference_answer_for_question = reference_answers[question_number]
                question_score = score_answer(student_answer, reference_answer_for_question)

                if file_name not in results:
                    results[file_name] = {}

                results[file_name][f"question_{question_number}"] = {"score": question_score}

                total_score += question_score  # 累加每个题目的得分

        # 最终评分：根据题目数算每个题目的比例，然后给出总分100的评分
        final_score = (total_score / (total_questions * 100)) * 100  # 标准化并按100分计算

        # 构建最终的返回响应
        response = make_response({
            "score": final_score,
            "completed": True,
            "category": "半开放",
            "studentId": student_id,
            "homeworkId": homework_id,
            "homeworkName": homework_name
        })
        response.mimetype = "application/json"
        return response
