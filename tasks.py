import os

from flask import make_response
from openai import OpenAI
from app import get_model
import numpy as np
import sqlite3

# 加载预训练的 Sentence-BERT 模型
model = get_model()

BASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
DB_PATH = os.path.join(BASE_DIR, "assignments.db")

# OpenAI GPT 模型评分
def evaluate_with_gpt(filename):
    client = OpenAI(
        # This is the default and can be omitted
        api_key="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",
    )

    # 读取文件内容
    with open(filename, 'r') as file:
        content = file.read()

    # 调用 GPT 模型进行评分
    prompt = f"""
       请根据以下标准为这篇数据库作业打分，并确保评分在1到100之间。请在第一行给出整体评分，并解释为什么给出这个分数。

       评分标准：
       1. 数据库设计的合理性
       2. SQL 查询的正确性
       3. 数据库优化的考虑

       请在第一行只给出一个数字评分（1-100），并说明评分理由。

       作业内容：
       {content}
       """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # 使用适合的模型 gpt-3.5-turbo 或 gpt-4
        messages=[
            {"role": "system", "content": "你是一个数据库作业评分专家。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    # 获取所有行并打印
    all_responses = [choice.message.content.strip() for choice in completion.choices]
    full_response = "\n".join(all_responses)  # 将所有行合并为一个字符串
    print(full_response)  # 打印所有返回的消息内容
    return full_response


# 生成作业特征向量
def generate_feature_vector(filename):
    with open(filename, 'r') as file:
        content = file.read()
    # 生成特征向量
    embedding = model.encode(content)
    return embedding


# 确保表存在
def ensure_table_exists(cursor, homework_name):
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS "{homework_name}" (
            student_id INTEGER PRIMARY KEY,
            embedding BLOB
        )
    """)


# 存储特征向量到数据库
def store_feature_vector(cursor, embedding, homework_name, student_id):
    ensure_table_exists(cursor, homework_name)
    cursor.execute(f"""
        INSERT OR REPLACE INTO "{homework_name}" (student_id, embedding)
        VALUES (?, ?)
    """, (student_id, sqlite3.Binary(np.array(embedding, dtype=np.float32).tobytes())))


# 查重：计算相似度
def check_similarity(cursor, embedding, homework_name):
    ensure_table_exists(cursor, homework_name)
    cursor.execute(f'SELECT student_id, embedding FROM "{homework_name}"')
    assignments = cursor.fetchall()

    similarities = []
    for stored_student_id, stored_embedding in assignments:
        stored_embedding = np.frombuffer(stored_embedding, dtype=np.float32)
        similarity = np.dot(embedding, stored_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored_embedding))
        # 将相似度映射到 0 到 100%的范围
        similarity_percentage = (similarity + 1) * 50  # 将 [-1, 1] 映射到 [0, 100]
        similarities.append((stored_student_id, similarity_percentage))

    # 查重：选择相似度最高的作业
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_similarity = similarities[0] if similarities else None

    # 返回一部字典，包含相似度百分比
    if top_similarity:
        return {
            'file': top_similarity[0],
            'similarity': top_similarity[1]
        }
    else:
        return None


def extract_score_from_first_line(first_line):
    for word in first_line.split():
        try:
            return int(word)  # 尝试将单词转换为整数并返回
        except ValueError:
            continue  # 如果无法转换为数字，继续处理下一个单词

    return 0  # 如果没有找到数字，返回0


# Celery 任务：处理文件
def process_assignment_task(filename, student_id, homework_id, homework_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 在这里调用大语言模型评分和查重
    score_description = evaluate_with_gpt(filename)
    first_line = score_description.split('\n')[0]
    score = extract_score_from_first_line(first_line)
    description = "\n".join(score_description.split('\n'))
    embedding = generate_feature_vector(filename)

    store_feature_vector(cursor, embedding, homework_name, student_id)
    similarity = check_similarity(cursor, embedding, homework_name)
    print(similarity)

    conn.commit()  # 提交事务（如果有写操作）
    cursor.close()  # 先关 cursor
    conn.close()  # 再关 conn

    response = make_response({
        "score": score,
        "completed": True,
        "category": "主观题",
        "studentId": student_id,
        "homeworkId": homework_id,
        "homeworkName": homework_name,
        "description": description
    })

    return response
