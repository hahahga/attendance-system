/**
 * 考勤系统主JavaScript文件
 * 包含通用功能、工具函数和全局事件处理
 */

// 全局变量
window.AttendanceSystem = {
    // API基础URL
    apiBaseUrl: '/api/v1',
    
    // 当前用户信息
    currentUser: null,
    
    // 系统配置
    config: {},
    
    // 初始化函数
    init: function() {
        this.loadCurrentUser();
        this.loadSystemConfig();
        this.bindGlobalEvents();
        this.initTooltips();
        this.initPopovers();
        this.checkNotifications();
    },
    
    // 加载当前用户信息
    loadCurrentUser: function() {
        const self = this;
        axios.get(`${self.apiBaseUrl}/auth/current-user`)
            .then(response => {
                self.currentUser = response.data;
                self.updateUserInterface();
            })
            .catch(error => {
                console.error('加载用户信息失败:', error);
                // 如果获取用户信息失败，可能是未登录，重定向到登录页
                if (error.response && error.response.status === 401) {
                    window.location.href = '/login';
                }
            });
    },
    
    // 加载系统配置
    loadSystemConfig: function() {
        const self = this;
        axios.get(`${self.apiBaseUrl}/system/config`)
            .then(response => {
                self.config = response.data;
                self.applySystemConfig();
            })
            .catch(error => {
                console.error('加载系统配置失败:', error);
            });
    },
    
    // 更新用户界面
    updateUserInterface: function() {
        if (!this.currentUser) return;
        
        // 更新用户名显示
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(el => {
            el.textContent = this.currentUser.name || this.currentUser.username;
        });
        
        // 更新用户头像
        const userAvatarElements = document.querySelectorAll('.user-avatar');
        userAvatarElements.forEach(el => {
            if (this.currentUser.avatar) {
                el.src = this.currentUser.avatar;
            }
        });
        
        // 更新用户角色显示
        const userRoleElements = document.querySelectorAll('.user-role');
        userRoleElements.forEach(el => {
            el.textContent = this.getRoleDisplayName(this.currentUser.role);
        });
        
        // 根据角色显示/隐藏菜单项
        this.updateMenuByRole();
    },
    
    // 获取角色显示名称
    getRoleDisplayName: function(role) {
        const roleMap = {
            'admin': '管理员',
            'manager': '部门经理',
            'hr': '人事',
            'employee': '员工'
        };
        return roleMap[role] || '未知';
    },
    
    // 根据角色更新菜单
    updateMenuByRole: function() {
        if (!this.currentUser) return;
        
        const role = this.currentUser.role;
        
        // 管理员可见菜单项
        const adminOnlyItems = document.querySelectorAll('.admin-only');
        adminOnlyItems.forEach(item => {
            item.style.display = role === 'admin' ? '' : 'none';
        });
        
        // 管理员和人事可见菜单项
        const adminHrItems = document.querySelectorAll('.admin-hr-only');
        adminHrItems.forEach(item => {
            item.style.display = (role === 'admin' || role === 'hr') ? '' : 'none';
        });
        
        // 管理员和经理可见菜单项
        const adminManagerItems = document.querySelectorAll('.admin-manager-only');
        adminManagerItems.forEach(item => {
            item.style.display = (role === 'admin' || role === 'manager') ? '' : 'none';
        });
    },
    
    // 应用系统配置
    applySystemConfig: function() {
        // 应用系统名称
        if (this.config.system_name) {
            const systemNameElements = document.querySelectorAll('.system-name');
            systemNameElements.forEach(el => {
                el.textContent = this.config.system_name;
            });
            
            document.title = this.config.system_name;
        }
        
        // 应用主题颜色
        if (this.config.primary_color) {
            document.documentElement.style.setProperty('--primary-color', this.config.primary_color);
        }
        
        // 应用公司Logo
        if (this.config.company_logo) {
            const logoElements = document.querySelectorAll('.company-logo');
            logoElements.forEach(el => {
                el.src = this.config.company_logo;
            });
        }
    },
    
    // 绑定全局事件
    bindGlobalEvents: function() {
        // 处理表单提交
        document.addEventListener('submit', function(e) {
            const form = e.target;
            if (form.classList.contains('ajax-form')) {
                e.preventDefault();
                AttendanceSystem.handleAjaxForm(form);
            }
        });
        
        // 处理确认对话框
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('confirm-action')) {
                e.preventDefault();
                const message = e.target.getAttribute('data-message') || '确定要执行此操作吗？';
                if (confirm(message)) {
                    window.location.href = e.target.getAttribute('href');
                }
            }
        });
        
        // 处理表格行点击
        document.addEventListener('click', function(e) {
            const row = e.target.closest('.clickable-row');
            if (row && !e.target.closest('button, a, input')) {
                const url = row.getAttribute('data-url');
                if (url) {
                    window.location.href = url;
                }
            }
        });
        
        // 处理全选复选框
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('select-all')) {
                const checkboxes = document.querySelectorAll(e.target.getAttribute('data-target'));
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
            }
        });
        
        // 处理文件上传预览
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('file-upload-preview')) {
                AttendanceSystem.handleFileUploadPreview(e.target);
            }
        });
        
        // 处理日期时间选择器
        document.addEventListener('focusin', function(e) {
            if (e.target.classList.contains('datetime-picker')) {
                AttendanceSystem.initDateTimePicker(e.target);
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
    
    // 初始化弹出框
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },
    
    // 处理AJAX表单提交
    handleAjaxForm: function(form) {
        const self = this;
        const url = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';
        const formData = new FormData(form);
        
        // 显示加载状态
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>处理中...';
        
        axios({
            method: method,
            url: url,
            data: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            self.showToast(response.data.message || '操作成功', 'success');
            
            // 如果表单有重定向URL，则跳转
            const redirectUrl = form.getAttribute('data-redirect');
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000);
            } else if (response.data.redirect) {
                setTimeout(() => {
                    window.location.href = response.data.redirect;
                }, 1000);
            } else {
                // 重置表单
                form.reset();
            }
        })
        .catch(error => {
            let errorMessage = '操作失败';
            
            if (error.response && error.response.data) {
                if (error.response.data.detail) {
                    errorMessage = error.response.data.detail;
                } else if (error.response.data.message) {
                    errorMessage = error.response.data.message;
                }
                
                // 处理表单验证错误
                if (error.response.data.errors) {
                    self.displayFormErrors(form, error.response.data.errors);
                }
            }
            
            self.showToast(errorMessage, 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    },
    
    // 显示表单验证错误
    displayFormErrors: function(form, errors) {
        // 清除之前的错误
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
        
        // 显示新的错误
        for (const field in errors) {
            const fieldEl = form.querySelector(`[name="${field}"]`);
            if (fieldEl) {
                fieldEl.classList.add('is-invalid');
                
                const feedbackEl = document.createElement('div');
                feedbackEl.className = 'invalid-feedback';
                feedbackEl.textContent = Array.isArray(errors[field]) ? errors[field].join(', ') : errors[field];
                
                fieldEl.parentNode.appendChild(feedbackEl);
            }
        }
    },
    
    // 处理文件上传预览
    handleFileUploadPreview: function(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewId = input.getAttribute('data-preview');
                if (previewId) {
                    const preview = document.getElementById(previewId);
                    if (preview) {
                        if (preview.tagName === 'IMG') {
                            preview.src = e.target.result;
                        } else {
                            preview.style.backgroundImage = `url(${e.target.result})`;
                        }
                    }
                }
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    },
    
    // 初始化日期时间选择器
    initDateTimePicker: function(element) {
        // 如果已经初始化过，则不再初始化
        if (element._flatpickr) {
            return;
        }
        
        const options = {
            enableTime: element.classList.contains('datetime-picker'),
            dateFormat: element.classList.contains('datetime-picker') 
                ? 'Y-m-d H:i' 
                : 'Y-m-d',
            locale: 'zh',
            time_24hr: true
        };
        
        // 如果有最小日期限制
        if (element.hasAttribute('data-min-date')) {
            options.minDate = element.getAttribute('data-min-date');
        }
        
        // 如果有最大日期限制
        if (element.hasAttribute('data-max-date')) {
            options.maxDate = element.getAttribute('data-max-date');
        }
        
        // 初始化flatpickr
        element._flatpickr = flatpickr(element, options);
    },
    
    // 显示提示消息
    showToast: function(message, type = 'info') {
        // 创建toast容器（如果不存在）
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1050';
            document.body.appendChild(toastContainer);
        }
        
        // 创建toast元素
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        // 添加到容器
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 显示toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 5000
        });
        
        toast.show();
        
        // 监听隐藏事件，移除DOM元素
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    },
    
    // 检查通知
    checkNotifications: function() {
        const self = this;
        
        // 每5分钟检查一次新通知
        setInterval(function() {
            axios.get(`${self.apiBaseUrl}/notifications/unread-count`)
                .then(response => {
                    const count = response.data.count || 0;
                    self.updateNotificationBadge(count);
                })
                .catch(error => {
                    console.error('检查通知失败:', error);
                });
        }, 300000); // 5分钟
        
        // 页面加载时立即检查一次
        axios.get(`${self.apiBaseUrl}/notifications/unread-count`)
            .then(response => {
                const count = response.data.count || 0;
                self.updateNotificationBadge(count);
            })
            .catch(error => {
                console.error('检查通知失败:', error);
            });
    },
    
    // 更新通知徽章
    updateNotificationBadge: function(count) {
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? '' : 'none';
        });
    },
    
    // 格式化日期时间
    formatDateTime: function(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    },
    
    // 格式化日期
    formatDate: function(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    },
    
    // 格式化时间
    formatTime: function(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${hours}:${minutes}`;
    },
    
    // 计算时间差
    getTimeDifference: function(startTime, endTime) {
        if (!startTime || !endTime) return '';
        
        const start = new Date(startTime);
        const end = new Date(endTime);
        const diff = end - start;
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        return `${hours}小时${minutes}分钟`;
    },
    
    // 下载文件
    downloadFile: function(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    // 确认对话框
    confirmDialog: function(message, callback) {
        if (confirm(message)) {
            if (typeof callback === 'function') {
                callback();
            }
        }
    },
    
    // 加载页面内容
    loadPageContent: function(url, containerId, callback) {
        const self = this;
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.error(`容器 #${containerId} 不存在`);
            return;
        }
        
        // 显示加载状态
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">加载中...</p>
            </div>
        `;
        
        axios.get(url)
            .then(response => {
                container.innerHTML = response.data;
                
                // 重新初始化工具提示和弹出框
                self.initTooltips();
                self.initPopovers();
                
                // 执行回调
                if (typeof callback === 'function') {
                    callback(response.data);
                }
            })
            .catch(error => {
                console.error('加载页面内容失败:', error);
                container.innerHTML = `
                    <div class="alert alert-danger">
                        加载内容失败: ${error.response?.data?.detail || '未知错误'}
                    </div>
                `;
            });
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    AttendanceSystem.init();
});

// 导出全局对象
window.ATT = window.AttendanceSystem;