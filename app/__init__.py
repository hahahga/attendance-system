"""
考勤系统应用包
"""

__version__ = "1.0.0"

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify, make_response, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# 配置MySQL连接器
import pymysql
pymysql.install_as_MySQLdb()

def create_app(config=None):
    """
    创建Flask应用实例
    
    Args:
        config: 配置字典，用于覆盖默认配置
        
    Returns:
        Flask应用实例
    """
    # 创建Flask应用，指定模板和静态文件夹路径
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # 加载默认配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///./data/database/attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 加载邮件配置
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    
    # 应用传入的配置
    if config:
        app.config.update(config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    # 自定义匿名用户类
    class AnonymousUser:
        def __init__(self):
            self.username = 'Anonymous'
            self.is_admin = False
            self.department = None
            self.id = None  # 添加id属性以解决AnonymousUser object has no attribute 'id'错误
        
        def is_authenticated(self):
            return False
        
        def is_active(self):
            return False
        
        def is_anonymous(self):
            return True
        
        def get_id(self):
            return None
    
    login_manager.anonymous_user = AnonymousUser
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User, UserRole
        return User.query.get(int(user_id))
    
    # 注册路由
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            from app.models.user import User
            username = request.form.get('username')
            password = request.form.get('password')
            
            # 查找用户
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/attendance/clock_in', methods=['POST'])
    @login_required
    @csrf.exempt
    def clock_in():
        from datetime import datetime, date
        from app.models.attendance import Attendance, AttendanceStatus
        
        # 检查今日是否已签到
        today = date.today()
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if attendance and attendance.check_in_time:
            return jsonify({'success': False, 'detail': '今日已签到'})
        else:
            if not attendance:
                attendance = Attendance(
                    user_id=current_user.id,
                    date=today
                )
                db.session.add(attendance)
            
            attendance.check_in_time = datetime.now()
            attendance.status = AttendanceStatus.PRESENT
            db.session.commit()
            return jsonify({'success': True, 'detail': '签到成功', 'time': attendance.check_in_time.strftime('%H:%M:%S')})
    
    @app.route('/attendance/clock_out', methods=['POST'])
    @login_required
    @csrf.exempt
    def clock_out():
        from datetime import datetime, date
        from app.models.attendance import Attendance, AttendanceStatus
        
        # 检查今日是否已签到
        today = date.today()
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not attendance or not attendance.check_in_time:
            return jsonify({'success': False, 'detail': '请先签到'})
        elif attendance.check_out_time:
            return jsonify({'success': False, 'detail': '今日已签退'})
        else:
            attendance.check_out_time = datetime.now()
            attendance.calculate_work_hours()
            db.session.commit()
            return jsonify({'success': True, 'detail': '签退成功', 'time': attendance.check_out_time.strftime('%H:%M:%S')})
    
    @app.route('/attendance/face_clock_in', methods=['POST'])
    @login_required
    @csrf.exempt
    def face_clock_in():
        from datetime import datetime, date
        from app.models.attendance import Attendance, AttendanceStatus
        from app.models.user import User
        import base64
        import io
        from PIL import Image
        import face_recognition
        import numpy as np
        import tempfile
        import os
        
        # 获取用户信息
        user = User.query.get(current_user.id)
        if not user or not user.face_encoding:
            return jsonify({'success': False, 'detail': '用户不存在或未注册人脸'})
        
        # 获取上传的图像数据
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'success': False, 'detail': '未提供图像数据'})
        
        # 解码base64图像
        try:
            # 去除base64前缀
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # 将base64转换为图像
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 转换为numpy数组
            image_array = np.array(image)
            
            # 检测人脸
            face_locations = face_recognition.face_locations(image_array)
            if not face_locations:
                return jsonify({'success': False, 'detail': '未检测到人脸'})
            
            # 提取人脸编码
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            if not face_encodings:
                return jsonify({'success': False, 'detail': '无法提取人脸特征'})
            
            # 加载已知人脸编码
            known_face_encoding = np.array(eval(user.face_encoding))
            
            # 比较人脸
            face_distances = face_recognition.face_distance([known_face_encoding], face_encodings[0])
            face_match_percentage = (1 - face_distances[0]) * 100
            
            # 设置人脸识别阈值
            if face_match_percentage < 70:  # 70%的匹配度阈值
                return jsonify({'success': False, 'detail': f'人脸识别失败，匹配度: {face_match_percentage:.2f}%'})
            
            # 人脸识别成功，执行签到
            today = date.today()
            attendance = Attendance.query.filter_by(
                user_id=current_user.id,
                date=today
            ).first()
            
            if attendance and attendance.check_in_time:
                return jsonify({'success': False, 'detail': '今日已签到'})
            else:
                # 获取位置信息
                location_data = request.json.get('location', {})
                location_address = location_data.get('address', '未知位置')
                
                if not attendance:
                    attendance = Attendance(
                        user_id=current_user.id,
                        date=today
                    )
                    db.session.add(attendance)
                
                attendance.check_in_time = datetime.now()
                attendance.check_in_location = location_address
                attendance.status = AttendanceStatus.PRESENT
                db.session.commit()
                return jsonify({'success': True, 'message': '人脸识别签到成功', 'time': attendance.check_in_time.strftime('%H:%M:%S'), 'location': location_address})
                
        except Exception as e:
            return jsonify({'success': False, 'detail': f'人脸识别失败: {str(e)}'})
    
    @app.route('/attendance/face_clock_out', methods=['POST'])
    @login_required
    @csrf.exempt
    def face_clock_out():
        from datetime import datetime, date
        from app.models.attendance import Attendance
        from app.models.user import User
        import base64
        import io
        from PIL import Image
        import face_recognition
        import numpy as np
        import tempfile
        import os
        
        # 获取用户信息
        user = User.query.get(current_user.id)
        if not user or not user.face_encoding:
            return jsonify({'success': False, 'detail': '用户不存在或未注册人脸'})
        
        # 获取上传的图像数据
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'success': False, 'detail': '未提供图像数据'})
        
        # 解码base64图像
        try:
            # 去除base64前缀
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            # 将base64转换为图像
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 转换为numpy数组
            image_array = np.array(image)
            
            # 检测人脸
            face_locations = face_recognition.face_locations(image_array)
            if not face_locations:
                return jsonify({'success': False, 'detail': '未检测到人脸'})
            
            # 提取人脸编码
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            if not face_encodings:
                return jsonify({'success': False, 'detail': '无法提取人脸特征'})
            
            # 加载已知人脸编码
            known_face_encoding = np.array(eval(user.face_encoding))
            
            # 比较人脸
            face_distances = face_recognition.face_distance([known_face_encoding], face_encodings[0])
            face_match_percentage = (1 - face_distances[0]) * 100
            
            # 设置人脸识别阈值
            if face_match_percentage < 70:  # 70%的匹配度阈值
                return jsonify({'success': False, 'detail': f'人脸识别失败，匹配度: {face_match_percentage:.2f}%'})
            
            # 人脸识别成功，执行签退
            today = date.today()
            attendance = Attendance.query.filter_by(
                user_id=current_user.id,
                date=today
            ).first()
            
            if not attendance or not attendance.check_in_time:
                return jsonify({'success': False, 'detail': '请先签到'})
            elif attendance.check_out_time:
                return jsonify({'success': False, 'detail': '今日已签退'})
            else:
                # 获取位置信息
                location_data = request.json.get('location', {})
                location_address = location_data.get('address', '未知位置')
                
                attendance.check_out_time = datetime.now()
                attendance.check_out_location = location_address
                attendance.calculate_work_hours()
                db.session.commit()
                return jsonify({'success': True, 'detail': '人脸识别签退成功', 'time': attendance.check_out_time.strftime('%H:%M:%S'), 'location': location_address})
                
        except Exception as e:
            return jsonify({'success': False, 'detail': f'人脸识别失败: {str(e)}'})
    
    @app.route('/attendance/history')
    @login_required
    def attendance_history():
        from app.models.attendance import Attendance
        attendances = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
        return render_template('attendance_history.html', attendances=attendances)
    
    @app.route('/attendance/calendar')
    @login_required
    def attendance_calendar():
        return render_template('attendance_calendar.html')
    
    @app.route('/attendance/team')
    @login_required
    def attendance_team():
        from app.models.user import User, UserRole
        from app.models.attendance import Attendance
        
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.HR]:
            return render_template('403.html'), 403
        
        # 获取团队成员的考勤记录
        if current_user.role == UserRole.MANAGER and current_user.department_id:
            users = User.query.filter_by(department_id=current_user.department_id).all()
        else:
            users = User.query.all()
        
        user_ids = [user.id for user in users]
        attendances = Attendance.query.filter(Attendance.user_id.in_(user_ids)).order_by(Attendance.date.desc()).all()
        
        return render_template('attendance_team.html', attendances=attendances)
    
    @app.route('/admin/attendance')
    @login_required
    def admin_attendance():
        from app.models.user import User
        from app.models.attendance import Attendance
        
        if current_user.role != UserRole.ADMIN:
            return render_template('403.html'), 403
        
        attendances = Attendance.query.order_by(Attendance.date.desc()).all()
        return render_template('admin_attendance.html', attendances=attendances)
    
    @app.route('/admin/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_attendance(attendance_id):
        from app.models.user import User
        from app.models.attendance import Attendance
        
        if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
            return render_template('403.html'), 403
        
        attendance = Attendance.query.get_or_404(attendance_id)
        
        if request.method == 'POST':
            # 更新考勤记录
            check_in_date = request.form.get('check_in_date')
            check_in_time = request.form.get('check_in_time')
            check_out_time = request.form.get('check_out_time')
            status = request.form.get('status')
            note = request.form.get('note')
            
            if check_in_date and check_in_time:
                from datetime import datetime
                attendance.check_in_time = datetime.strptime(f"{check_in_date} {check_in_time}", "%Y-%m-%d %H:%M")
            
            if check_out_time:
                from datetime import datetime, date
                attendance.check_out_time = datetime.strptime(f"{check_in_date} {check_out_time}", "%Y-%m-%d %H:%M")
            
            attendance.status = status
            attendance.notes = note
            attendance.calculate_work_hours()
            
            db.session.commit()
            flash('考勤记录更新成功')
            return redirect(url_for('admin_attendance'))
        
        return render_template('edit_attendance.html', attendance=attendance)
    
    @app.route('/admin/attendance/<int:attendance_id>/delete', methods=['POST'])
    @login_required
    def delete_attendance(attendance_id):
        from app.models.attendance import Attendance
        from app.models.user import UserRole
        
        if current_user.role not in [UserRole.ADMIN, UserRole.HR]:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        attendance = Attendance.query.get_or_404(attendance_id)
        db.session.delete(attendance)
        db.session.commit()
        
        return jsonify({'success': True})
    
    # 考勤页面
    @app.route('/attendance')
    @login_required
    def attendance():
        return render_template('attendance.html')
    
    # 人脸识别签到页面
    @app.route('/attendance/face_clock_in')
    @login_required
    def face_clock_in_page():
        return render_template('face_clock_in.html')
    
    # 人脸识别签退页面
    @app.route('/attendance/face_clock_out')
    @login_required
    def face_clock_out_page():
        return render_template('face_clock_out.html')
    
    # 请假页面
    @app.route('/leave')
    @login_required
    def leave():
        return render_template('leave.html')
    
    # 申请请假页面
    @app.route('/leave/apply')
    @login_required
    def leave_apply():
        return render_template('leave_apply.html')
    
    # 请假记录页面
    @app.route('/leave/history')
    @login_required
    def leave_history():
        return render_template('leave_history.html')
    
    # 个人资料页面
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')
    
    # 修改密码页面
    @app.route('/change-password')
    @login_required
    def change_password():
        return render_template('change_password.html')
    
    # API端点
    
    # 获取今日考勤状态
    @app.route('/api/today_attendance')
    @login_required
    def api_today_attendance():
        from datetime import date, datetime
        from app.models.attendance import Attendance, AttendanceStatus
        
        today = date.today()
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        result = {
            'check_in_time': None,
            'check_out_time': None,
            'work_hours': None,
            'status': '未签到'
        }
        
        if attendance:
            if attendance.check_in_time:
                result['check_in_time'] = attendance.check_in_time.strftime('%H:%M:%S')
            
            if attendance.check_out_time:
                result['check_out_time'] = attendance.check_out_time.strftime('%H:%M:%S')
            
            if attendance.work_hours:
                hours = int(attendance.work_hours)
                minutes = int((attendance.work_hours - hours) * 60)
                result['work_hours'] = f"{hours}小时{minutes}分钟"
            
            # 根据枚举值返回对应的中文字符串
            if attendance.status == AttendanceStatus.PRESENT:
                result['status'] = '正常'
            elif attendance.status == AttendanceStatus.LATE:
                result['status'] = '迟到'
            elif attendance.status == AttendanceStatus.EARLY_LEAVE:
                result['status'] = '早退'
            elif attendance.status == AttendanceStatus.ABSENT:
                result['status'] = '缺勤'
            elif attendance.status == AttendanceStatus.LEAVE:
                result['status'] = '请假'
            else:
                result['status'] = attendance.status.value if attendance.status else '未签到'
        
        return result
    
    # 获取最近考勤记录
    @app.route('/api/recent_attendance')
    @login_required
    def api_recent_attendance():
        from datetime import date, timedelta
        from app.models.attendance import Attendance, AttendanceStatus
        
        # 获取最近7天的考勤记录
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        attendances = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date.desc()).all()
        
        data = []
        for attendance in attendances:
            # 将枚举值转换为中文字符串
            status_str = '未签到'
            if attendance.status == AttendanceStatus.PRESENT:
                status_str = '正常'
            elif attendance.status == AttendanceStatus.LATE:
                status_str = '迟到'
            elif attendance.status == AttendanceStatus.EARLY_LEAVE:
                status_str = '早退'
            elif attendance.status == AttendanceStatus.ABSENT:
                status_str = '缺勤'
            elif attendance.status == AttendanceStatus.LEAVE:
                status_str = '请假'
            
            data.append({
                'date': attendance.date.strftime('%Y-%m-%d'),
                'day': attendance.date.strftime('%A'),
                'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else None,
                'status': status_str,
                'work_hours': attendance.work_hours
            })
        
        return jsonify(data)
    
    # 获取本周统计
    @app.route('/api/week_statistics')
    @login_required
    def api_week_statistics():
        from datetime import date, timedelta, datetime
        from app.models.attendance import Attendance, AttendanceStatus
        
        # 获取本周的起止日期
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # 获取本周考勤记录
        attendances = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.date >= start_of_week,
            Attendance.date <= end_of_week
        ).all()
        
        # 计算统计数据
        total_days = len(attendances)
        present_days = len([a for a in attendances if a.status == AttendanceStatus.PRESENT])
        late_days = len([a for a in attendances if a.status == AttendanceStatus.LATE])
        absent_days = len([a for a in attendances if a.status == AttendanceStatus.ABSENT])
        
        # 计算总工作时长
        total_hours = sum([a.work_hours for a in attendances if a.work_hours])
        
        return jsonify({
            'total_days': total_days,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'total_hours': round(total_hours, 2),
            'attendance_rate': round(present_days / 7 * 100, 1) if total_days > 0 else 0
        })
    
    # 获取请假统计
    @app.route('/api/leave_statistics')
    @login_required
    def api_leave_statistics():
        from datetime import date
        from app.models.leave import Leave
        
        # 获取今年的请假记录
        current_year = date.today().year
        leave_requests = Leave.query.filter(
            Leave.user_id == current_user.id,
            Leave.start_date >= date(current_year, 1, 1),
            Leave.start_date <= date(current_year, 12, 31)
        ).all()
        
        # 按类型统计
        sick_leave = sum([lr.days for lr in leave_requests if lr.leave_type.value == 'sick'])
        personal_leave = sum([lr.days for lr in leave_requests if lr.leave_type.value == 'personal'])
        annual_leave = sum([lr.days for lr in leave_requests if lr.leave_type.value == 'annual'])
        
        return jsonify({
            'sick_leave': sick_leave,
            'personal_leave': personal_leave,
            'annual_leave': annual_leave,
            'total_leave': sick_leave + personal_leave + annual_leave
        })
    
    # 获取最近请假记录
    @app.route('/api/recent_leave')
    @login_required
    def api_recent_leave():
        from app.models.leave import Leave
        
        # 获取最近的请假记录
        leave_requests = Leave.query.filter_by(
            user_id=current_user.id
        ).order_by(Leave.applied_at.desc()).limit(5).all()
        
        data = []
        for leave in leave_requests:
            data.append({
                'id': leave.id,
                'leave_type': leave.leave_type.value,
                'start_date': leave.start_date.strftime('%Y-%m-%d'),
                'end_date': leave.end_date.strftime('%Y-%m-%d'),
                'days': leave.days,
                'reason': leave.reason[:50] + '...' if len(leave.reason) > 50 else leave.reason,
                'status': leave.status.value,
                'created_at': leave.applied_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify(data)
    
    # 修改密码
    @app.route('/api/change_password', methods=['POST'])
    @login_required
    def api_change_password():
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return {'success': False, 'message': '请输入当前密码和新密码'}
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            return {'success': False, 'message': '当前密码不正确', 'field': 'current_password'}
        
        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        return {'success': True, 'message': '密码修改成功'}
    
    # 获取月度考勤数据
    @app.route('/api/month_attendance')
    @login_required
    def api_month_attendance():
        from datetime import date, timedelta
        from app.models.attendance import Attendance
        
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        attendances = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        result = []
        for attendance in attendances:
            item = {
                'date': attendance.date.strftime('%Y-%m-%d'),
                'status': attendance.status or 'absent'
            }
            result.append(item)
        
        return jsonify(result)
    
    # 获取月度统计
    @app.route('/api/month_statistics')
    @login_required
    def api_month_statistics():
        from datetime import date, timedelta
        from app.models.attendance import Attendance, AttendanceStatus
        
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        attendances = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        result = {
            'present': 0,
            'late': 0,
            'early': 0,
            'leave': 0
        }
        
        for attendance in attendances:
            if attendance.status == AttendanceStatus.PRESENT:
                result['present'] += 1
            elif attendance.status == AttendanceStatus.LATE:
                result['late'] += 1
            elif attendance.status == AttendanceStatus.EARLY_LEAVE:
                result['early'] += 1
            elif attendance.status == AttendanceStatus.LEAVE:
                result['leave'] += 1
        
        return jsonify(result)
    
    # 获取团队考勤
    @app.route('/api/team_attendance')
    @login_required
    def api_team_attendance():
        from datetime import date, timedelta
        from app.models.user import User
        from app.models.attendance import Attendance, AttendanceStatus
        
        filter_type = request.args.get('filter', 'today')
        
        if filter_type == 'today':
            target_date = date.today()
        elif filter_type == 'week':
            target_date = date.today()
        elif filter_type == 'month':
            target_date = date.today()
        else:
            target_date = date.today()
        
        # 获取所有用户（简化版，实际应根据部门或其他条件筛选）
        users = User.query.all()
        
        result = []
        for user in users:
            user_data = {
                'id': user.id,
                'name': user.username,
                'department': '技术部',  # 简化处理
                'today_status': 'absent',
                'clock_in_time': None,
                'clock_out_time': None,
                'work_hours': None,
                'month_present': 0,
                'month_leave': 0
            }
            
            # 查询今日考勤
            if filter_type in ['today', 'week', 'month']:
                attendance = Attendance.query.filter_by(
                    user_id=user.id,
                    date=target_date
                ).first()
                
                if attendance:
                    user_data['today_status'] = attendance.status.value if attendance.status else 'absent'
                    if attendance.check_in_time:
                        user_data['clock_in_time'] = attendance.check_in_time.strftime('%H:%M')
                    if attendance.check_out_time:
                        user_data['clock_out_time'] = attendance.check_out_time.strftime('%H:%M')
                    if attendance.work_hours:
                        hours = int(attendance.work_hours)
                        minutes = int((attendance.work_hours - hours) * 60)
                        user_data['work_hours'] = f"{hours}h {minutes}m"
            
            # 查询本月统计
            start_of_month = date(target_date.year, target_date.month, 1)
            month_attendances = Attendance.query.filter(
                Attendance.user_id == user.id,
                Attendance.date >= start_of_month,
                Attendance.date <= target_date
            ).all()
            
            for att in month_attendances:
                if att.status == AttendanceStatus.PRESENT:
                    user_data['month_present'] += 1
                elif att.status == AttendanceStatus.LEAVE:
                    user_data['month_leave'] += 1
            
            result.append(user_data)
        
        return jsonify(result)
    
    # 获取团队统计
    @app.route('/api/team_statistics')
    @login_required
    def api_team_statistics():
        from datetime import date, timedelta
        from app.models.user import User
        from app.models.attendance import Attendance, AttendanceStatus
        
        today = date.today()
        
        # 今日统计
        today_attendances = Attendance.query.filter_by(date=today).all()
        total_users = User.query.count()
        today_present = sum(1 for att in today_attendances if att.status == AttendanceStatus.PRESENT)
        today_rate = int((today_present / total_users) * 100) if total_users > 0 else 0
        
        # 本周统计
        start_of_week = today - timedelta(days=today.weekday())
        week_attendances = Attendance.query.filter(
            Attendance.date >= start_of_week,
            Attendance.date <= today
        ).all()
        week_present = sum(1 for att in week_attendances if att.status == AttendanceStatus.PRESENT)
        week_rate = int((week_present / (total_users * (today.weekday() + 1))) * 100) if total_users > 0 and today.weekday() >= 0 else 0
        
        # 本月统计
        start_of_month = date(today.year, today.month, 1)
        month_attendances = Attendance.query.filter(
            Attendance.date >= start_of_month,
            Attendance.date <= today
        ).all()
        month_present = sum(1 for att in month_attendances if att.status == AttendanceStatus.PRESENT)
        month_rate = int((month_present / (total_users * today.day)) * 100) if total_users > 0 and today.day > 0 else 0
        
        return jsonify({
            'today': {
                'present': today_present,
                'rate': today_rate
            },
            'week': {
                'present': week_present,
                'rate': week_rate
            },
            'month': {
                'present': month_present,
                'rate': month_rate
            }
        })
    
    # 管理员获取考勤记录
    @app.route('/api/admin_attendance')
    @login_required
    def api_admin_attendance():
        from app.models.user import User
        from app.models.attendance import Attendance, AttendanceStatus
        
        page = request.args.get('page', 1, type=int)
        per_page = 20
        employee_id = request.args.get('employee_id')
        department_id = request.args.get('department_id')
        status = request.args.get('status')
        date = request.args.get('date')
        
        # 构建查询
        query = Attendance.query
        
        if employee_id:
            query = query.filter(Attendance.user_id == employee_id)
        
        if status:
            # 将字符串状态转换为枚举值
            if status == 'present':
                query = query.filter(Attendance.status == AttendanceStatus.PRESENT)
            elif status == 'late':
                query = query.filter(Attendance.status == AttendanceStatus.LATE)
            elif status == 'early_leave':
                query = query.filter(Attendance.status == AttendanceStatus.EARLY_LEAVE)
            elif status == 'absent':
                query = query.filter(Attendance.status == AttendanceStatus.ABSENT)
            elif status == 'leave':
                query = query.filter(Attendance.status == AttendanceStatus.LEAVE)
        
        if date:
            query = query.filter(Attendance.date == date)
        
        # 分页
        pagination = query.order_by(Attendance.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 构建结果
        result = {
            'records': [],
            'total_pages': pagination.pages,
            'current_page': page
        }
        
        for attendance in pagination.items:
            user = User.query.get(attendance.user_id)
            
            record = {
                'id': attendance.id,
                'employee_id': user.id,
                'employee_name': user.username,
                'department_name': '技术部',  # 简化处理
                'date': attendance.date.strftime('%Y-%m-%d'),
                'clock_in_time': attendance.check_in_time.strftime('%H:%M:%S') if attendance.check_in_time else None,
                'clock_out_time': attendance.check_out_time.strftime('%H:%M:%S') if attendance.check_out_time else None,
                'work_hours': f"{attendance.work_hours}小时" if attendance.work_hours else None,
                'status': attendance.status.value if attendance.status else 'absent',
                'note': attendance.notes
            }
            
            result['records'].append(record)
        
        return jsonify(result)
    
    # 管理员获取单个考勤记录
    @app.route('/api/admin_attendance/<attendance_id>')
    @login_required
    def api_admin_attendance_detail(attendance_id):
        from app.models.user import User
        from app.models.attendance import Attendance
        
        attendance = Attendance.query.get(attendance_id)
        if not attendance:
            return jsonify({'error': '考勤记录不存在'}), 404
        
        user = User.query.get(attendance.user_id)
        
        return jsonify({
            'id': attendance.id,
            'employee_id': user.id,
            'date': attendance.date.strftime('%Y-%m-%d'),
            'clock_in_time': attendance.check_in_time.strftime('%H:%M:%S') if attendance.check_in_time else None,
            'clock_out_time': attendance.check_out_time.strftime('%H:%M:%S') if attendance.check_out_time else None,
            'work_hours': attendance.work_hours,
            'status': attendance.status.value if attendance.status else 'absent',
            'note': attendance.notes
        })
    
    # 管理员添加考勤记录
    @app.route('/api/admin_attendance', methods=['POST'])
    @login_required
    def api_admin_add_attendance():
        from datetime import datetime, date, time
        from app.models.attendance import Attendance
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        clock_in = data.get('clock_in_time')
        clock_out = data.get('clock_out_time')
        status = data.get('status')
        note = data.get('note')
        
        if not employee_id or not date_str or not status:
            return jsonify({'success': False, 'message': '请填写必要信息'})
        
        # 解析日期
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式不正确'})
        
        # 解析时间
        check_in_time = None
        check_out_time = None
        
        if clock_in:
            try:
                check_in_time = datetime.strptime(clock_in, '%H:%M:%S').time()
            except ValueError:
                try:
                    check_in_time = datetime.strptime(clock_in, '%H:%M').time()
                except ValueError:
                    return jsonify({'success': False, 'message': '签到时间格式不正确'})
        
        if clock_out:
            try:
                check_out_time = datetime.strptime(clock_out, '%H:%M:%S').time()
            except ValueError:
                try:
                    check_out_time = datetime.strptime(clock_out, '%H:%M').time()
                except ValueError:
                    return jsonify({'success': False, 'message': '签退时间格式不正确'})
        
        # 计算工作时长
        work_hours = None
        if check_in_time and check_out_time:
            in_minutes = check_in_time.hour * 60 + check_in_time.minute
            out_minutes = check_out_time.hour * 60 + check_out_time.minute
            
            if out_minutes > in_minutes:
                work_minutes = out_minutes - in_minutes
                work_hours = work_minutes / 60
            else:
                # 跨天情况
                next_day_minutes = 24 * 60 + out_minutes
                work_minutes = next_day_minutes - in_minutes
                work_hours = work_minutes / 60
        
        # 检查是否已存在记录
        existing = Attendance.query.filter_by(
            user_id=employee_id,
            date=attendance_date
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': '该员工在此日期已有考勤记录'})
        
        # 创建新记录
        attendance = Attendance(
            user_id=employee_id,
            date=attendance_date,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            work_hours=work_hours,
            status=status,
            notes=note
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '考勤记录添加成功'})
    
    # 管理员更新考勤记录
    @app.route('/api/admin_attendance/<attendance_id>', methods=['PUT'])
    @login_required
    def api_admin_update_attendance(attendance_id):
        from app.models.attendance import Attendance
        attendance = Attendance.query.get(attendance_id)
        if not attendance:
            return jsonify({'success': False, 'message': '考勤记录不存在'})
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        clock_in = data.get('clock_in_time')
        clock_out = data.get('clock_out_time')
        status = data.get('status')
        note = data.get('note')
        
        if not employee_id or not date_str or not status:
            return jsonify({'success': False, 'message': '请填写必要信息'})
        
        from datetime import datetime, date, time
        
        # 解析日期
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式不正确'})
        
        # 解析时间
        check_in_time = None
        check_out_time = None
        
        if clock_in:
            try:
                check_in_time = datetime.strptime(clock_in, '%H:%M:%S').time()
            except ValueError:
                try:
                    check_in_time = datetime.strptime(clock_in, '%H:%M').time()
                except ValueError:
                    return jsonify({'success': False, 'message': '签到时间格式不正确'})
        
        if clock_out:
            try:
                check_out_time = datetime.strptime(clock_out, '%H:%M:%S').time()
            except ValueError:
                try:
                    check_out_time = datetime.strptime(clock_out, '%H:%M').time()
                except ValueError:
                    return jsonify({'success': False, 'message': '签退时间格式不正确'})
        
        # 计算工作时长
        work_hours = None
        if check_in_time and check_out_time:
            in_minutes = check_in_time.hour * 60 + check_in_time.minute
            out_minutes = check_out_time.hour * 60 + check_out_time.minute
            
            if out_minutes > in_minutes:
                work_minutes = out_minutes - in_minutes
                work_hours = work_minutes / 60
            else:
                # 跨天情况
                next_day_minutes = 24 * 60 + out_minutes
                work_minutes = next_day_minutes - in_minutes
                work_hours = work_minutes / 60
        
        # 更新记录
        attendance.user_id = employee_id
        attendance.date = attendance_date
        attendance.check_in_time = check_in_time
        attendance.check_out_time = check_out_time
        attendance.work_hours = work_hours
        attendance.status = status
        attendance.notes = note
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '考勤记录更新成功'})
    
    # 管理员删除考勤记录
    @app.route('/api/admin_attendance/<attendance_id>', methods=['DELETE'])
    @login_required
    def api_admin_delete_attendance(attendance_id):
        from app.models.attendance import Attendance
        attendance = Attendance.query.get(attendance_id)
        if not attendance:
            return jsonify({'success': False, 'message': '考勤记录不存在'})
        
        db.session.delete(attendance)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '考勤记录删除成功'})
    
    # 获取员工列表
    @app.route('/api/employees')
    @login_required
    def api_employees():
        from app.models.user import User
        users = User.query.all()
        
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'name': user.username,
                'email': user.email
            })
        
        return jsonify(result)
    
    # 获取部门列表
    @app.route('/api/departments')
    @login_required
    def api_departments():
        # 简化处理，返回固定的部门列表
        return jsonify([
            {'id': 1, 'name': '技术部'},
            {'id': 2, 'name': '市场部'},
            {'id': 3, 'name': '人事部'},
            {'id': 4, 'name': '财务部'}
        ])
    
    # 导出考勤记录
    @app.route('/api/export_attendance')
    @login_required
    def api_export_attendance():
        from datetime import date
        from app.models.attendance import Attendance, AttendanceStatus
        from app.models.user import User
        employee_id = request.args.get('employee_id')
        department_id = request.args.get('department_id')
        status = request.args.get('status')
        date_str = request.args.get('date')
        
        # 构建查询
        query = Attendance.query
        
        if employee_id:
            query = query.filter(Attendance.user_id == employee_id)
        
        if status:
            # 将字符串状态转换为枚举值
            if status == 'present':
                query = query.filter(Attendance.status == AttendanceStatus.PRESENT)
            elif status == 'late':
                query = query.filter(Attendance.status == AttendanceStatus.LATE)
            elif status == 'early_leave':
                query = query.filter(Attendance.status == AttendanceStatus.EARLY_LEAVE)
            elif status == 'absent':
                query = query.filter(Attendance.status == AttendanceStatus.ABSENT)
            elif status == 'leave':
                query = query.filter(Attendance.status == AttendanceStatus.LEAVE)
        
        if date_str:
            query = query.filter(Attendance.date == date_str)
        
        # 获取所有记录
        attendances = query.order_by(Attendance.date.desc()).all()
        
        # 构建CSV数据
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            '员工ID', '员工姓名', '部门', '日期', '签到时间', '签退时间', '工作时长', '状态', '备注'
        ])
        
        # 写入数据
        for attendance in attendances:
            user = User.query.get(attendance.user_id)
            
            writer.writerow([
                user.id,
                user.username,
                '技术部',  # 简化处理
                attendance.date.strftime('%Y-%m-%d'),
                attendance.check_in_time.strftime('%H:%M:%S') if attendance.check_in_time else '',
                attendance.check_out_time.strftime('%H:%M:%S') if attendance.check_out_time else '',
                f"{attendance.work_hours}小时" if attendance.work_hours else '',
                attendance.status.value if attendance.status else '缺勤',
                attendance.notes or ''
            ])
        
        # 设置响应头
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_export_{date.today()}.csv'
        
        return response
    
    return app