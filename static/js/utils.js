/**
 * 考勤系统通用工具函数
 * 包含日期处理、数据验证、格式化等功能
 */

window.Utils = {
    // 日期相关函数
    date: {
        // 格式化日期
        format: function(date, format = 'YYYY-MM-DD') {
            if (!date) return '';
            
            const d = new Date(date);
            if (isNaN(d.getTime())) return '';
            
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
        
        // 获取当前日期
        today: function() {
            return this.format(new Date());
        },
        
        // 获取当前日期时间
        now: function() {
            return this.format(new Date(), 'YYYY-MM-DD HH:mm:ss');
        },
        
        // 获取本周开始日期
        weekStart: function() {
            const today = new Date();
            const day = today.getDay();
            const diff = today.getDate() - day + (day === 0 ? -6 : 1);
            const monday = new Date(today.setDate(diff));
            return this.format(monday);
        },
        
        // 获取本周结束日期
        weekEnd: function() {
            const today = new Date();
            const day = today.getDay();
            const diff = today.getDate() - day + (day === 0 ? 0 : 7);
            const sunday = new Date(today.setDate(diff));
            return this.format(sunday);
        },
        
        // 获取本月开始日期
        monthStart: function() {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            return this.format(firstDay);
        },
        
        // 获取本月结束日期
        monthEnd: function() {
            const today = new Date();
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            return this.format(lastDay);
        },
        
        // 获取本季度开始日期
        quarterStart: function() {
            const today = new Date();
            const quarter = Math.floor(today.getMonth() / 3);
            const firstMonth = quarter * 3;
            const firstDay = new Date(today.getFullYear(), firstMonth, 1);
            return this.format(firstDay);
        },
        
        // 获取本季度结束日期
        quarterEnd: function() {
            const today = new Date();
            const quarter = Math.floor(today.getMonth() / 3);
            const lastMonth = quarter * 3 + 2;
            const lastDay = new Date(today.getFullYear(), lastMonth + 1, 0);
            return this.format(lastDay);
        },
        
        // 获取本年开始日期
        yearStart: function() {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), 0, 1);
            return this.format(firstDay);
        },
        
        // 获取本年结束日期
        yearEnd: function() {
            const today = new Date();
            const lastDay = new Date(today.getFullYear(), 11, 31);
            return this.format(lastDay);
        },
        
        // 计算两个日期之间的天数差
        daysBetween: function(startDate, endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const diffTime = Math.abs(end - start);
            return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        },
        
        // 计算两个时间之间的时间差（小时:分钟）
        timeDifference: function(startTime, endTime) {
            if (!startTime || !endTime) return '';
            
            const start = new Date(`2000-01-01 ${startTime}`);
            const end = new Date(`2000-01-01 ${endTime}`);
            const diff = end - start;
            
            if (diff <= 0) return '';
            
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            return `${hours}小时${minutes}分钟`;
        },
        
        // 判断是否为工作日
        isWeekday: function(date) {
            const d = new Date(date);
            const day = d.getDay();
            return day !== 0 && day !== 6;
        },
        
        // 添加天数
        addDays: function(date, days) {
            const d = new Date(date);
            d.setDate(d.getDate() + days);
            return this.format(d);
        },
        
        // 减去天数
        subtractDays: function(date, days) {
            const d = new Date(date);
            d.setDate(d.getDate() - days);
            return this.format(d);
        }
    },
    
    // 数据验证函数
    validate: {
        // 验证邮箱
        email: function(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },
        
        // 验证手机号
        phone: function(phone) {
            const re = /^1[3-9]\d{9}$/;
            return re.test(phone);
        },
        
        // 验证身份证号
        idCard: function(idCard) {
            const re = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
            return re.test(idCard);
        },
        
        // 验证工号
        employeeId: function(employeeId) {
            const re = /^[A-Za-z0-9]{4,10}$/;
            return re.test(employeeId);
        },
        
        // 验证密码强度（至少8位，包含大小写字母和数字）
        password: function(password) {
            const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
            return re.test(password);
        },
        
        // 验证URL
        url: function(url) {
            try {
                new URL(url);
                return true;
            } catch (e) {
                return false;
            }
        },
        
        // 验证数字
        number: function(value) {
            return !isNaN(parseFloat(value)) && isFinite(value);
        },
        
        // 验证整数
        integer: function(value) {
            return Number.isInteger(Number(value));
        },
        
        // 验证正整数
        positiveInteger: function(value) {
            return this.integer(value) && Number(value) > 0;
        },
        
        // 验证日期
        date: function(date) {
            return !isNaN(new Date(date).getTime());
        },
        
        // 验证时间
        time: function(time) {
            const re = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
            return re.test(time);
        },
        
        // 验证日期时间
        datetime: function(datetime) {
            const re = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
            return re.test(datetime) && this.date(datetime);
        }
    },
    
    // 数据格式化函数
    format: {
        // 格式化文件大小
        fileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // 格式化数字（千分位）
        number: function(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        },
        
        // 格式化百分比
        percentage: function(num, decimals = 2) {
            return (num * 100).toFixed(decimals) + '%';
        },
        
        // 格式化货币
        currency: function(num, symbol = '¥') {
            return symbol + this.number(num.toFixed(2));
        },
        
        // 格式化手机号（隐藏中间4位）
        phone: function(phone) {
            if (!phone || phone.length !== 11) return phone;
            return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
        },
        
        // 格式化身份证号（隐藏部分数字）
        idCard: function(idCard) {
            if (!idCard || idCard.length < 8) return idCard;
            return idCard.substring(0, 4) + '**********' + idCard.substring(idCard.length - 4);
        },
        
        // 格式化时长（秒转换为小时:分钟:秒）
        duration: function(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            } else {
                return `${minutes}:${secs.toString().padStart(2, '0')}`;
            }
        },
        
        // 截断文本
        truncate: function(text, length, suffix = '...') {
            if (!text || text.length <= length) return text;
            return text.substring(0, length) + suffix;
        },
        
        // 首字母大写
        capitalize: function(text) {
            if (!text) return text;
            return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
        },
        
        // 驼峰命名转换为短横线命名
        camelToKebab: function(text) {
            return text.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
        },
        
        // 短横线命名转换为驼峰命名
        kebabToCamel: function(text) {
            return text.replace(/-([a-z])/g, function(g) {
                return g[1].toUpperCase();
            });
        }
    },
    
    // 数据转换函数
    convert: {
        // 字符串转数字
        toNumber: function(value, defaultValue = 0) {
            const num = parseFloat(value);
            return isNaN(num) ? defaultValue : num;
        },
        
        // 字符串转整数
        toInteger: function(value, defaultValue = 0) {
            const num = parseInt(value, 10);
            return isNaN(num) ? defaultValue : num;
        },
        
        // 字符串转布尔值
        toBoolean: function(value, defaultValue = false) {
            if (value === null || value === undefined || value === '') {
                return defaultValue;
            }
            
            if (typeof value === 'boolean') {
                return value;
            }
            
            if (typeof value === 'string') {
                const lowerValue = value.toLowerCase();
                return lowerValue === 'true' || lowerValue === '1' || lowerValue === 'yes' || lowerValue === 'on';
            }
            
            return Boolean(value);
        },
        
        // 数组转对象
        arrayToObject: function(array, keyField) {
            const obj = {};
            array.forEach(item => {
                if (item[keyField]) {
                    obj[item[keyField]] = item;
                }
            });
            return obj;
        },
        
        // 对象转数组
        objectToArray: function(obj) {
            return Object.keys(obj).map(key => ({
                key,
                value: obj[key]
            }));
        },
        
        // 深拷贝
        deepClone: function(obj) {
            if (obj === null || typeof obj !== 'object') {
                return obj;
            }
            
            if (obj instanceof Date) {
                return new Date(obj.getTime());
            }
            
            if (obj instanceof Array) {
                return obj.map(item => this.deepClone(item));
            }
            
            const cloned = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    cloned[key] = this.deepClone(obj[key]);
                }
            }
            
            return cloned;
        }
    },
    
    // DOM操作函数
    dom: {
        // 创建元素
        createElement: function(tag, attributes = {}, children = []) {
            const element = document.createElement(tag);
            
            // 设置属性
            for (const attr in attributes) {
                if (attr === 'className') {
                    element.className = attributes[attr];
                } else if (attr === 'innerHTML') {
                    element.innerHTML = attributes[attr];
                } else if (attr === 'textContent') {
                    element.textContent = attributes[attr];
                } else {
                    element.setAttribute(attr, attributes[attr]);
                }
            }
            
            // 添加子元素
            children.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else {
                    element.appendChild(child);
                }
            });
            
            return element;
        },
        
        // 查找元素
        find: function(selector, parent = document) {
            return parent.querySelector(selector);
        },
        
        // 查找所有元素
        findAll: function(selector, parent = document) {
            return Array.from(parent.querySelectorAll(selector));
        },
        
        // 添加类
        addClass: function(element, className) {
            if (element) {
                element.classList.add(className);
            }
        },
        
        // 移除类
        removeClass: function(element, className) {
            if (element) {
                element.classList.remove(className);
            }
        },
        
        // 切换类
        toggleClass: function(element, className) {
            if (element) {
                element.classList.toggle(className);
            }
        },
        
        // 检查是否包含类
        hasClass: function(element, className) {
            return element ? element.classList.contains(className) : false;
        },
        
        // 显示元素
        show: function(element) {
            if (element) {
                element.style.display = '';
            }
        },
        
        // 隐藏元素
        hide: function(element) {
            if (element) {
                element.style.display = 'none';
            }
        },
        
        // 获取元素位置
        getPosition: function(element) {
            if (!element) return { top: 0, left: 0 };
            
            const rect = element.getBoundingClientRect();
            return {
                top: rect.top + window.pageYOffset,
                left: rect.left + window.pageXOffset
            };
        },
        
        // 滚动到元素
        scrollTo: function(element, offset = 0) {
            if (!element) return;
            
            const position = this.getPosition(element);
            window.scrollTo({
                top: position.top - offset,
                behavior: 'smooth'
            });
        }
    },
    
    // URL操作函数
    url: {
        // 获取URL参数
        getParam: function(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        },
        
        // 获取所有URL参数
        getAllParams: function() {
            const urlParams = new URLSearchParams(window.location.search);
            const params = {};
            
            for (const [key, value] of urlParams) {
                params[key] = value;
            }
            
            return params;
        },
        
        // 设置URL参数
        setParam: function(name, value) {
            const url = new URL(window.location);
            url.searchParams.set(name, value);
            window.history.replaceState({}, '', url);
        },
        
        // 删除URL参数
        removeParam: function(name) {
            const url = new URL(window.location);
            url.searchParams.delete(name);
            window.history.replaceState({}, '', url);
        },
        
        // 构建URL
        build: function(base, params = {}) {
            const url = new URL(base);
            
            for (const key in params) {
                if (params[key] !== null && params[key] !== undefined) {
                    url.searchParams.set(key, params[key]);
                }
            }
            
            return url.toString();
        }
    },
    
    // 存储操作函数
    storage: {
        // 设置本地存储
        setLocal: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('设置本地存储失败:', e);
                return false;
            }
        },
        
        // 获取本地存储
        getLocal: function(key, defaultValue = null) {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : defaultValue;
            } catch (e) {
                console.error('获取本地存储失败:', e);
                return defaultValue;
            }
        },
        
        // 删除本地存储
        removeLocal: function(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('删除本地存储失败:', e);
                return false;
            }
        },
        
        // 清空本地存储
        clearLocal: function() {
            try {
                localStorage.clear();
                return true;
            } catch (e) {
                console.error('清空本地存储失败:', e);
                return false;
            }
        },
        
        // 设置会话存储
        setSession: function(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('设置会话存储失败:', e);
                return false;
            }
        },
        
        // 获取会话存储
        getSession: function(key, defaultValue = null) {
            try {
                const value = sessionStorage.getItem(key);
                return value ? JSON.parse(value) : defaultValue;
            } catch (e) {
                console.error('获取会话存储失败:', e);
                return defaultValue;
            }
        },
        
        // 删除会话存储
        removeSession: function(key) {
            try {
                sessionStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('删除会话存储失败:', e);
                return false;
            }
        }
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },
    
    // 节流函数
    throttle: function(func, wait) {
        let lastTime = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastTime >= wait) {
                lastTime = now;
                func.apply(this, args);
            }
        };
    },
    
    // 生成唯一ID
    generateId: function(prefix = '') {
        return prefix + Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // 生成随机颜色
    randomColor: function() {
        return '#' + Math.floor(Math.random()*16777215).toString(16);
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
    
    // 复制到剪贴板
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text)
                .then(() => {
                    window.ATT.showToast('已复制到剪贴板', 'success');
                })
                .catch(err => {
                    console.error('复制失败:', err);
                    window.ATT.showToast('复制失败', 'danger');
                });
        } else {
            // 兼容旧浏览器
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    window.ATT.showToast('已复制到剪贴板', 'success');
                } else {
                    window.ATT.showToast('复制失败', 'danger');
                }
            } catch (err) {
                console.error('复制失败:', err);
                document.body.removeChild(textArea);
                window.ATT.showToast('复制失败', 'danger');
            }
        }
    }
};

// 导出全局对象
window.UTILS = window.Utils;