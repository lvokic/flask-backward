import os
import logging
from flask import request, jsonify
from sentence_transformers import SentenceTransformer
from werkzeug.utils import secure_filename

model_path = os.path.join(os.path.dirname(__file__), 'model')
model = SentenceTransformer(model_path)

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 获取 logger 实例
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# 创建文件处理器
log_path = os.path.join(log_dir, 'template.log')
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


def get_model():
    return model


def save_student_homework(file, student_id, homework_name, folder):
    file_extension = os.path.splitext(file.filename)[1].lower()
    filename = f"{student_id}{homework_name}{file_extension}"
    filepath = os.path.join(folder, filename)

    if not os.path.exists(folder):
        os.makedirs(folder)

    file.save(filepath)


def handle_file_upload(folder):
    """
    通用的文件上传处理函数，适用于任何类型的文件上传。
    :param folder: 上传文件保存的文件夹
    :return: 文件上传的响应
    """
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    homework_name = request.form.get('homeworkName')

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    # 定义支持的文件扩展名
    allowed_extensions = ['.doc', '.docx', '.pdf', '.txt']
    # 获取文件扩展名
    file_extension = os.path.splitext(file.filename)[1].lower()

    # 检查文件扩展名是否在允许的类型中
    if file_extension not in allowed_extensions:
        return jsonify(
            {"message": f"Invalid file format. Only {', '.join(allowed_extensions)} files are allowed."}), 400

    # 确保上传目录存在
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 根据 homeworkName 重命名文件，避免文件名冲突
    filename = f"{homework_name}{file_extension}"
    filepath = os.path.join(folder, filename)

    # 如果文件已存在，删除并覆盖
    if os.path.exists(filepath):
        os.remove(filepath)  # 删除已存在的文件

    # 保存文件
    file.save(filepath)
    return jsonify({"message": "File uploaded successfully", "filename": file.filename}), 200
