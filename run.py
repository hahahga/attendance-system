#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考勤系统启动脚本
用于启动Flask应用服务器
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Department, SystemConfig
from app.models.user import UserRole


def init_database(app):
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 检查是否已有管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # 创建默认管理员用户
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='系统',
                last_name='管理员',
                full_name='系统管理员',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')  # 默认密码
            db.session.add(admin)
            print("创建默认管理员用户: admin/admin123")
        
        # 检查是否有默认部门
        default_dept = Department.query.filter_by(name='综合部').first()
        if not default_dept:
            # 创建默认部门
            dept = Department(
                name='综合部',
                code='ZH',
                description='系统默认部门'
            )
            db.session.add(dept)
            print("创建默认部门: 综合部")
        
        # 检查是否有系统配置
        config = SystemConfig.query.first()
        if not config:
            # 创建默认系统配置
            config = SystemConfig(
                system_name='考勤管理系统',
                company_name='示例公司',
                work_start_time='09:00',
                work_end_time='18:00',
                late_threshold=10,
                early_threshold=10,
                work_days='1,2,3,4,5',  # 周一到周五
                allow_face_recognition=True,
                allow_leave=True,
                allow_overtime=True,
                notification_enabled=True,
                auto_backup=True,
                backup_retention_days=30
            )
            db.session.add(config)
            print("创建默认系统配置")
        
        # 提交所有更改
        db.session.commit()
        print("数据库初始化完成")


def create_sample_data(app):
    """创建示例数据"""
    with app.app_context():
        # 创建示例部门
        departments = [
            {'name': '技术部', 'code': 'JS', 'description': '负责技术开发和维护'},
            {'name': '人事部', 'code': 'RS', 'description': '负责人力资源管理'},
            {'name': '财务部', 'code': 'CW', 'description': '负责财务管理'},
            {'name': '市场部', 'code': 'SC', 'description': '负责市场推广'}
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(name=dept_data['name']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
        
        # 创建示例用户
        users = [
            {
                'username': 'manager',
                'email': 'manager@example.com',
                'name': '部门经理',
                'password': 'manager123',
                'role': UserRole.MANAGER,
                'department_name': '技术部'
            },
            {
                'username': 'hr',
                'email': 'hr@example.com',
                'name': '人事专员',
                'password': 'hr123',
                'role': UserRole.HR,
                'department_name': '人事部'
            },
            {
                'username': 'employee1',
                'email': 'employee1@example.com',
                'name': '员工1',
                'password': 'emp123',
                'role': UserRole.EMPLOYEE,
                'department_name': '技术部'
            },
            {
                'username': 'employee2',
                'email': 'employee2@example.com',
                'name': '员工2',
                'password': 'emp123',
                'role': UserRole.EMPLOYEE,
                'department_name': '市场部'
            }
        ]
        
        for user_data in users:
            user = User.query.filter_by(username=user_data['username']).first()
            if not user:
                department = Department.query.filter_by(name=user_data.pop('department_name')).first()
                
                # 将full_name拆分为first_name和last_name
                full_name = user_data['name']
                if len(full_name) > 1:
                    first_name = full_name[0]
                    last_name = full_name[1:]
                else:
                    first_name = full_name
                    last_name = ""
                
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=first_name,
                    last_name=last_name,
                    full_name=user_data['name'],
                    role=user_data['role'],
                    department_id=department.id if department else None,
                    is_active=True
                )
                user.set_password(user_data.pop('password'))
                db.session.add(user)
        
        db.session.commit()
        print("示例数据创建完成")


def backup_database(app):
    """备份数据库"""
    from datetime import datetime
    import subprocess
    
    with app.app_context():
        # 获取数据库连接信息
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        
        # 检查是否为MySQL数据库
        if 'mysql' in database_url:
            # 解析MySQL连接信息
            import re
            match = re.match(r'mysql://(\w+):([^@]+)@([^:]+):(\d+)/(\w+)', database_url)
            if match:
                username, password, host, port, database = match.groups()
                
                # 创建备份目录
                backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # 创建备份文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f'attendance_backup_{timestamp}.sql')
                
                # 使用mysqldump命令备份数据库
                try:
                    command = f'mysqldump -u{username} -p{password} -h{host} -P{port} {database} > {backup_path}'
                    subprocess.run(command, shell=True, check=True)
                    print(f"MySQL数据库备份完成: {backup_path}")
                except subprocess.CalledProcessError as e:
                    print(f"数据库备份失败: {e}")
                except FileNotFoundError:
                    print("mysqldump命令未找到，请确保MySQL客户端工具已安装并添加到PATH")
            else:
                print("无法解析MySQL连接字符串")
        else:
            # SQLite数据库备份逻辑
            import shutil
            db_path = app.config.get('DATABASE_PATH', 'attendance.db')
            
            if os.path.exists(db_path):
                # 创建备份目录
                backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # 创建备份文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f'attendance_backup_{timestamp}.db')
                
                # 复制数据库文件
                shutil.copy2(db_path, backup_path)
                print(f"SQLite数据库备份完成: {backup_path}")
            else:
                print(f"数据库文件不存在: {db_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='考勤管理系统启动脚本')
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    parser.add_argument('--create-sample-data', action='store_true', help='创建示例数据')
    parser.add_argument('--backup-db', action='store_true', help='备份数据库')
    
    args = parser.parse_args()
    
    # 创建应用实例
    app = create_app()
    
    # 初始化数据库
    if args.init_db:
        init_database(app)
        if not args.create_sample_data:
            print("数据库初始化完成，使用 --create-sample-data 参数可以创建示例数据")
            return
    
    # 创建示例数据
    if args.create_sample_data:
        init_database(app)  # 确保数据库已初始化
        create_sample_data(app)
        print("示例数据创建完成")
        return
    
    # 备份数据库
    if args.backup_db:
        backup_database(app)
        return
    
    # 启动服务器
    print(f"启动考勤管理系统服务器...")
    print(f"服务器地址: http://{args.host}:{args.port}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )


if __name__ == '__main__':
    main()