/**
 * 考勤系统通用JavaScript函数
 */

// 全局变量
window.App = {
    // API基础URL
    apiBaseUrl: '/api',
    
    // 当前用户信息
    currentUser: null,
    
    // 初始化函数
    init: function() {
        this.bindEvents();
        this.initTooltips();
        this.initModals();
        this.checkAuthentication();
    },
    
    // 绑定事件
    bindEvents: function() {
        // 通用表单提交事件
        document.addEventListener('submit', function(e) {
            const form = e.target;
            if (form.classList.contains('ajax-form')) {
                e.preventDefault();
                App.submitAjaxForm(form);
            }
        });
        
        // 通用确认按钮事件
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('confirm-action')) {
                e.preventDefault();
                const message = e.target.getAttribute('data-message') || '确定要执行此操作吗？';
                const url = e.target.getAttribute('href') || e.target.getAttribute('data-url');
                
                if (url) {
                    App.confirmAction(message, url);
                }
            }
        });
    },
    
    // 初始化工具提示
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // 初始化模态框
    initModals: function() {
        const commonModal = document.getElementById('commonModal');
        if (commonModal) {
            this.commonModal = new bootstrap.Modal(commonModal);
        }
    },
    
    // 检查用户认证状态
    checkAuthentication: function() {
        // 这里可以添加检查用户认证状态的逻辑
    },
    
    // 显示提示消息
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // 自动移除
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    },
    
    // 显示确认对话框
    confirmAction: function(message, url) {
        if (!this.commonModal) return;
        
        document.getElementById('commonModalTitle').textContent = '确认操作';
        document.getElementById('commonModalBody').textContent = message;
        
        const confirmBtn = document.getElementById('commonModalConfirm');
        confirmBtn.onclick = function() {
            App.commonModal.hide();
            App.executeAction(url);
        };
        
        this.commonModal.show();
    },
    
    // 执行操作
    executeAction: function(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    App.showToast(data.message || '操作成功', 'success');
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    } else if (data.reload) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                } else {
                    App.showToast(data.message || '操作失败', 'error');
                }
            })
            .catch(error => {
                console.error('操作出错:', error);
                App.showToast('操作出错，请稍后再试', 'error');
            });
    },
    
    // 提交AJAX表单
    submitAjaxForm: function(form) {
        const url = form.getAttribute('action') || window.location.href;
        const method = form.getAttribute('method') || 'POST';
        const formData = new FormData(form);
        
        // 显示加载状态
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>处理中...';
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    App.showToast(data.message || '操作成功', 'success');
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    } else if (data.reload) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                } else {
                    App.showToast(data.message || '操作失败', 'error');
                    // 显示表单验证错误
                    if (data.errors) {
                        App.showFormErrors(form, data.errors);
                    }
                }
            })
            .catch(error => {
                console.error('表单提交出错:', error);
                App.showToast('表单提交出错，请稍后再试', 'error');
            })
            .finally(() => {
                // 恢复按钮状态
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
    },
    
    // 显示表单验证错误
    showFormErrors: function(form, errors) {
        // 清除之前的错误
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
        
        // 显示新的错误
        for (const field in errors) {
            const fieldElement = form.querySelector(`[name="${field}"]`);
            if (fieldElement) {
                fieldElement.classList.add('is-invalid');
                
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = Array.isArray(errors[field]) ? errors[field].join(', ') : errors[field];
                
                fieldElement.parentNode.appendChild(feedback);
            }
        }
    },
    
    // 格式化日期
    formatDate: function(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },
    
    // 格式化时间
    formatTime: function(time) {
        if (!time) return '';
        
        const d = new Date(time);
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        return `${hours}:${minutes}`;
    },
    
    // 考勤相关函数
    attendance: {
        // 签到
        clockIn: function() {
            App.executeAction('/attendance/clock_in', 'POST');
        },
        
        // 签退
        clockOut: function() {
            App.executeAction('/attendance/clock_out', 'POST');
        },
        
        // 获取今日考勤状态
        getTodayStatus: function() {
            fetch('/api/today_attendance')
                .then(response => response.json())
                .then(data => {
                    // 更新页面上的考勤状态显示
                    const statusElement = document.getElementById('attendance-status');
                    if (statusElement) {
                        statusElement.textContent = data.status;
                    }
                    
                    const checkInElement = document.getElementById('check-in-time');
                    if (checkInElement) {
                        checkInElement.textContent = data.check_in_time || '--:--:--';
                    }
                    
                    const checkOutElement = document.getElementById('check-out-time');
                    if (checkOutElement) {
                        checkOutElement.textContent = data.check_out_time || '--:--:--';
                    }
                    
                    const workHoursElement = document.getElementById('work-hours');
                    if (workHoursElement) {
                        workHoursElement.textContent = data.work_hours || '0小时';
                    }
                })
                .catch(error => {
                    console.error('获取考勤状态失败:', error);
                });
        },
        
        // 获取最近考勤记录
        getRecentRecords: function() {
            fetch('/api/recent_attendance')
                .then(response => response.json())
                .then(data => {
                    // 更新页面上的考勤记录显示
                    const tableBody = document.getElementById('recent-attendance-tbody');
                    if (tableBody) {
                        tableBody.innerHTML = '';
                        
                        data.forEach(record => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${record.date}</td>
                                <td>${record.day}</td>
                                <td>${record.check_in_time || '--'}</td>
                                <td>${record.check_out_time || '--'}</td>
                                <td>${record.work_hours ? record.work_hours + '小时' : '--'}</td>
                                <td><span class="attendance-status status-${record.status}">${record.status}</span></td>
                            `;
                            tableBody.appendChild(row);
                        });
                    }
                })
                .catch(error => {
                    console.error('获取考勤记录失败:', error);
                });
        }
    },
    
    // 请假相关函数
    leave: {
        // 申请请假
        apply: function(formData) {
            App.executeAction('/leave/apply', 'POST', formData);
        },
        
        // 获取请假记录
        getHistory: function() {
            fetch('/api/leave_history')
                .then(response => response.json())
                .then(data => {
                    // 更新页面上的请假记录显示
                    const tableBody = document.getElementById('leave-history-tbody');
                    if (tableBody) {
                        tableBody.innerHTML = '';
                        
                        data.forEach(record => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${record.start_date} 至 ${record.end_date}</td>
                                <td>${record.leave_type}</td>
                                <td>${record.days}天</td>
                                <td><span class="badge bg-${record.status === 'approved' ? 'success' : record.status === 'rejected' ? 'danger' : 'warning'}">${record.status}</span></td>
                                <td>${record.reason}</td>
                            `;
                            tableBody.appendChild(row);
                        });
                    }
                })
                .catch(error => {
                    console.error('获取请假记录失败:', error);
                });
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    App.init();
    
    // 如果是考勤页面，获取考勤状态
    if (window.location.pathname === '/attendance' || window.location.pathname === '/') {
        App.attendance.getTodayStatus();
        App.attendance.getRecentRecords();
    }
    
    // 如果是请假页面，获取请假记录
    if (window.location.pathname === '/leave/history') {
        App.leave.getHistory();
    }
});