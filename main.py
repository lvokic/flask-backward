import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from app.upload_handler import handle_template_objective_file_upload, submit_homework_objective, \
    handle_template_subjective_file_upload, handle_problem_objective_file_upload, handle_problem_subjective_file_upload, \
    handle_problem_open_file_upload
from app.rank_subjective_handler import score
from db import close_db
from app.tasks import process_assignment_task

# 创建Flask应用
app = Flask(__name__)
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 路由和视图函数
@app.route('/api/upload/template/objective', methods=['GET', 'POST'])
def upload_template_objective_file():
    # 调用上传处理函数，处理模板文件上传
    return handle_template_objective_file_upload()


@app.route('/api/upload/submit/objective', methods=['GET', 'POST'])
def upload_homework_objective_file():
    # 调用提交作业处理函数
    return submit_homework_objective()


@app.route('/api/upload/template/subjective', methods=['GET', 'POST'])
def upload_template_subjective_file():
    # 调用上传处理函数，处理模板文件上传
    return handle_template_subjective_file_upload()


@app.route('/api/upload/submit/subjective', methods=['GET', 'POST'])
def upload_homework_subjective_file():
    # 获取上传的文件
    student_id = request.form.get('studentId')  # 获取学生ID
    homework_id = request.form.get('homeworkID')  # 获取作业ID
    homework_name = request.form.get('homeworkName')
    file = request.files['file']

    return score(file, student_id, homework_id, homework_name)


# ----------------------------------  -问题上传模块- -------------------------------------#
@app.route('/api/upload/problem/objective', methods=['GET', 'POST'])
def upload_problem_objective_file():
    return handle_problem_objective_file_upload()


@app.route('/api/upload/problem/subjective', methods=['GET', 'POST'])
def upload_problem_subjective_file():
    return handle_problem_subjective_file_upload()


@app.route('/api/upload/problem/open', methods=['GET', 'POST'])
def upload_problem_open_file():
    return handle_problem_open_file_upload()


# ----------------------------------  -问题上传模块- -------------------------------------#


@app.route('/api/upload/submit/open', methods=['GET', 'POST'])
def upload_homework_open_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 使用 secure_filename 处理文件名
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # 获取上传的文件
    student_id = request.form.get('studentId')  # 获取学生ID
    homework_id = request.form.get('homeworkID')  # 获取作业ID
    homework_name = request.form.get('homeworkName')

    task = process_assignment_task(filepath, student_id, homework_id, homework_name)
    return task


@app.teardown_appcontext
def close_db_connection(exception):
    close_db()


if __name__ == '__main__':
    app.run(debug=True)
