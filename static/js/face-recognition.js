/**
 * 人脸识别相关JavaScript功能
 * 包含人脸检测、识别、注册等功能
 */

window.FaceRecognition = {
    // 视频元素
    video: null,
    
    // Canvas元素
    canvas: null,
    
    // 上下文
    context: null,
    
    // 视频流
    stream: null,
    
    // 人脸检测模型
    faceDetectionModel: null,
    
    // 人脸识别模型
    faceRecognitionModel: null,
    
    // 当前检测到的人脸
    currentFaces: [],
    
    // 是否正在检测
    isDetecting: false,
    
    // 检测间隔ID
    detectionInterval: null,
    
    // 初始化函数
    init: function() {
        this.video = document.getElementById('face-video');
        this.canvas = document.getElementById('face-canvas');
        this.context = this.canvas ? this.canvas.getContext('2d') : null;
        
        this.bindEvents();
        this.loadModels();
    },
    
    // 绑定事件
    bindEvents: function() {
        const self = this;
        
        // 启动摄像头按钮
        const startCameraBtn = document.getElementById('start-camera');
        if (startCameraBtn) {
            startCameraBtn.addEventListener('click', function() {
                self.startCamera();
            });
        }
        
        // 停止摄像头按钮
        const stopCameraBtn = document.getElementById('stop-camera');
        if (stopCameraBtn) {
            stopCameraBtn.addEventListener('click', function() {
                self.stopCamera();
            });
        }
        
        // 开始检测按钮
        const startDetectionBtn = document.getElementById('start-detection');
        if (startDetectionBtn) {
            startDetectionBtn.addEventListener('click', function() {
                self.startDetection();
            });
        }
        
        // 停止检测按钮
        const stopDetectionBtn = document.getElementById('stop-detection');
        if (stopDetectionBtn) {
            stopDetectionBtn.addEventListener('click', function() {
                self.stopDetection();
            });
        }
        
        // 拍照按钮
        const captureBtn = document.getElementById('capture-photo');
        if (captureBtn) {
            captureBtn.addEventListener('click', function() {
                self.capturePhoto();
            });
        }
        
        // 注册人脸按钮
        const registerFaceBtn = document.getElementById('register-face');
        if (registerFaceBtn) {
            registerFaceBtn.addEventListener('click', function() {
                self.registerFace();
            });
        }
        
        // 识别考勤按钮
        const recognizeAttendanceBtn = document.getElementById('recognize-attendance');
        if (recognizeAttendanceBtn) {
            recognizeAttendanceBtn.addEventListener('click', function() {
                self.recognizeAttendance();
            });
        }
        
        // 选择文件上传
        const fileInput = document.getElementById('face-image-upload');
        if (fileInput) {
            fileInput.addEventListener('change', function(e) {
                self.handleImageUpload(e);
            });
        }
    },
    
    // 加载模型
    loadModels: function() {
        const self = this;
        
        // 显示加载状态
        const statusEl = document.getElementById('model-status');
        if (statusEl) {
            statusEl.textContent = '正在加载模型...';
        }
        
        // 加载人脸检测模型
        Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/static/models'),
            faceapi.nets.faceExpressionNet.loadFromUri('/static/models')
        ])
        .then(function() {
            self.faceDetectionModel = faceapi.nets.tinyFaceDetector;
            self.faceRecognitionModel = faceapi.nets.faceRecognitionNet;
            
            if (statusEl) {
                statusEl.textContent = '模型加载完成';
            }
            
            console.log('人脸识别模型加载完成');
        })
        .catch(function(error) {
            console.error('加载模型失败:', error);
            
            if (statusEl) {
                statusEl.textContent = '模型加载失败';
            }
            
            // 如果使用face-api.js失败，尝试使用后端API
            self.initBackendAPI();
        });
    },
    
    // 初始化后端API
    initBackendAPI: function() {
        console.log('使用后端API进行人脸识别');
        
        const statusEl = document.getElementById('model-status');
        if (statusEl) {
            statusEl.textContent = '使用后端API';
        }
    },
    
    // 启动摄像头
    startCamera: function() {
        const self = this;
        
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(stream) {
                    self.stream = stream;
                    self.video.srcObject = stream;
                    
                    // 更新UI状态
                    document.getElementById('start-camera').disabled = true;
                    document.getElementById('stop-camera').disabled = false;
                    document.getElementById('camera-status').textContent = '摄像头已启动';
                })
                .catch(function(error) {
                    console.error('无法访问摄像头:', error);
                    window.ATT.showToast('无法访问摄像头，请检查权限设置', 'danger');
                });
        } else {
            window.ATT.showToast('您的浏览器不支持摄像头功能', 'warning');
        }
    },
    
    // 停止摄像头
    stopCamera: function() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.video.srcObject = null;
            this.stream = null;
            
            // 停止检测
            this.stopDetection();
            
            // 更新UI状态
            document.getElementById('start-camera').disabled = false;
            document.getElementById('stop-camera').disabled = true;
            document.getElementById('camera-status').textContent = '摄像头已停止';
        }
    },
    
    // 开始人脸检测
    startDetection: function() {
        if (!this.stream) {
            window.ATT.showToast('请先启动摄像头', 'warning');
            return;
        }
        
        this.isDetecting = true;
        
        // 更新UI状态
        document.getElementById('start-detection').disabled = true;
        document.getElementById('stop-detection').disabled = false;
        document.getElementById('detection-status').textContent = '检测中...';
        
        // 设置canvas尺寸
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // 开始检测循环
        this.detectionInterval = setInterval(() => {
            this.detectFaces();
        }, 100);
    },
    
    // 停止人脸检测
    stopDetection: function() {
        this.isDetecting = false;
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        
        // 清除canvas
        if (this.context) {
            this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        // 更新UI状态
        document.getElementById('start-detection').disabled = false;
        document.getElementById('stop-detection').disabled = true;
        document.getElementById('detection-status').textContent = '检测已停止';
    },
    
    // 检测人脸
    detectFaces: function() {
        const self = this;
        
        // 如果使用face-api.js
        if (this.faceDetectionModel) {
            this.detectFacesWithFaceAPI();
        } else {
            // 使用后端API
            this.detectFacesWithBackend();
        }
    },
    
    // 使用face-api.js检测人脸
    detectFacesWithFaceAPI: async function() {
        const self = this;
        
        try {
            const detections = await faceapi.detectAllFaces(
                this.video, 
                new faceapi.TinyFaceDetectorOptions()
            )
            .withFaceLandmarks()
            .withFaceExpressions();
            
            // 清除canvas
            this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            // 绘制检测结果
            detections.forEach(detection => {
                const box = detection.detection.box;
                
                // 绘制人脸框
                this.context.strokeStyle = '#00ff00';
                this.context.lineWidth = 2;
                this.context.strokeRect(box.x, box.y, box.width, box.height);
                
                // 绘制表情
                const expressions = detection.expressions;
                const maxExpression = Object.keys(expressions).reduce((a, b) => 
                    expressions[a] > expressions[b] ? a : b
                );
                
                this.context.fillStyle = '#00ff00';
                this.context.font = '16px Arial';
                this.context.fillText(maxExpression, box.x, box.y - 5);
            });
            
            this.currentFaces = detections;
            
            // 更新UI
            document.getElementById('face-count').textContent = detections.length;
            
        } catch (error) {
            console.error('人脸检测失败:', error);
        }
    },
    
    // 使用后端API检测人脸
    detectFacesWithBackend: function() {
        const self = this;
        
        // 将视频帧转换为图像
        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // 将canvas转换为base64图像
        const imageData = this.canvas.toDataURL('image/jpeg');
        
        // 发送到后端进行检测
        axios.post('/api/v1/face/detect', {
            image: imageData
        })
        .then(response => {
            const faces = response.data.faces || [];
            
            // 清除canvas
            self.context.clearRect(0, 0, self.canvas.width, self.canvas.height);
            
            // 重新绘制视频帧
            self.context.drawImage(self.video, 0, 0, self.canvas.width, self.canvas.height);
            
            // 绘制人脸框
            self.context.strokeStyle = '#00ff00';
            self.context.lineWidth = 2;
            
            faces.forEach(face => {
                self.context.strokeRect(
                    face.x, 
                    face.y, 
                    face.width, 
                    face.height
                );
                
                // 如果有识别结果，显示姓名
                if (face.name) {
                    self.context.fillStyle = '#00ff00';
                    self.context.font = '16px Arial';
                    self.context.fillText(face.name, face.x, face.y - 5);
                }
            });
            
            self.currentFaces = faces;
            
            // 更新UI
            document.getElementById('face-count').textContent = faces.length;
            
        })
        .catch(error => {
            console.error('人脸检测失败:', error);
        });
    },
    
    // 拍照
    capturePhoto: function() {
        if (!this.stream) {
            window.ATT.showToast('请先启动摄像头', 'warning');
            return;
        }
        
        // 设置canvas尺寸
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // 绘制当前视频帧
        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // 获取图像数据
        const imageData = this.canvas.toDataURL('image/jpeg');
        
        // 显示预览
        const preview = document.getElementById('photo-preview');
        if (preview) {
            preview.src = imageData;
        }
        
        // 保存图像数据到隐藏字段
        const imageField = document.getElementById('face-image-data');
        if (imageField) {
            imageField.value = imageData;
        }
        
        window.ATT.showToast('拍照成功', 'success');
    },
    
    // 注册人脸
    registerFace: function() {
        const imageData = document.getElementById('face-image-data').value;
        const userId = document.getElementById('user-id').value;
        
        if (!imageData) {
            window.ATT.showToast('请先拍照或上传人脸照片', 'warning');
            return;
        }
        
        if (!userId) {
            window.ATT.showToast('请选择用户', 'warning');
            return;
        }
        
        // 显示加载状态
        const registerBtn = document.getElementById('register-face');
        const originalText = registerBtn.textContent;
        registerBtn.disabled = true;
        registerBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>注册中...';
        
        // 发送注册请求
        axios.post('/api/v1/face/register', {
            user_id: userId,
            image: imageData
        })
        .then(response => {
            window.ATT.showToast('人脸注册成功', 'success');
            
            // 清空表单
            document.getElementById('face-image-data').value = '';
            document.getElementById('photo-preview').src = '';
            
            // 刷新人脸数据列表
            this.loadFaceData();
        })
        .catch(error => {
            const errorMessage = error.response?.data?.detail || '人脸注册失败';
            window.ATT.showToast(errorMessage, 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            registerBtn.disabled = false;
            registerBtn.textContent = originalText;
        });
    },
    
    // 人脸识别考勤
    recognizeAttendance: function() {
        if (!this.stream) {
            window.ATT.showToast('请先启动摄像头', 'warning');
            return;
        }
        
        if (this.currentFaces.length === 0) {
            window.ATT.showToast('未检测到人脸', 'warning');
            return;
        }
        
        // 设置canvas尺寸
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // 绘制当前视频帧
        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // 获取图像数据
        const imageData = this.canvas.toDataURL('image/jpeg');
        
        // 显示加载状态
        const recognizeBtn = document.getElementById('recognize-attendance');
        const originalText = recognizeBtn.textContent;
        recognizeBtn.disabled = true;
        recognizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>识别中...';
        
        // 发送识别请求
        axios.post('/api/v1/face/recognize', {
            image: imageData
        })
        .then(response => {
            const result = response.data;
            
            if (result.success) {
                window.ATT.showToast(`识别成功，${result.action}时间：${result.time}`, 'success');
                
                // 显示识别结果
                const resultDiv = document.getElementById('recognition-result');
                if (resultDiv) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>识别成功</h5>
                            <p><strong>姓名：</strong>${result.name}</p>
                            <p><strong>工号：</strong>${result.employee_id}</p>
                            <p><strong>操作：</strong>${result.action}</p>
                            <p><strong>时间：</strong>${result.time}</p>
                        </div>
                    `;
                }
                
                // 播放成功提示音
                this.playSound('success');
            } else {
                window.ATT.showToast(result.message || '识别失败', 'warning');
                
                // 播放失败提示音
                this.playSound('error');
            }
        })
        .catch(error => {
            const errorMessage = error.response?.data?.detail || '人脸识别失败';
            window.ATT.showToast(errorMessage, 'danger');
            
            // 播放错误提示音
            this.playSound('error');
        })
        .finally(() => {
            // 恢复按钮状态
            recognizeBtn.disabled = false;
            recognizeBtn.textContent = originalText;
        });
    },
    
    // 处理图片上传
    handleImageUpload: function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // 检查文件类型
        if (!file.type.match('image.*')) {
            window.ATT.showToast('请选择图片文件', 'warning');
            return;
        }
        
        // 检查文件大小（限制为5MB）
        if (file.size > 5 * 1024 * 1024) {
            window.ATT.showToast('图片大小不能超过5MB', 'warning');
            return;
        }
        
        const reader = new FileReader();
        const self = this;
        
        reader.onload = function(e) {
            const imageData = e.target.result;
            
            // 显示预览
            const preview = document.getElementById('photo-preview');
            if (preview) {
                preview.src = imageData;
            }
            
            // 保存图像数据到隐藏字段
            const imageField = document.getElementById('face-image-data');
            if (imageField) {
                imageField.value = imageData;
            }
            
            // 如果有canvas，也在canvas上显示
            if (self.canvas && self.context) {
                const img = new Image();
                img.onload = function() {
                    self.canvas.width = img.width;
                    self.canvas.height = img.height;
                    self.context.drawImage(img, 0, 0);
                };
                img.src = imageData;
            }
        };
        
        reader.readAsDataURL(file);
    },
    
    // 加载人脸数据
    loadFaceData: function() {
        const self = this;
        
        axios.get('/api/v1/face/data')
            .then(response => {
                const faceData = response.data.data || [];
                self.renderFaceDataTable(faceData);
            })
            .catch(error => {
                console.error('加载人脸数据失败:', error);
            });
    },
    
    // 渲染人脸数据表格
    renderFaceDataTable: function(faceData) {
        const tableBody = document.getElementById('face-data-table-body');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (faceData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">暂无人脸数据</td></tr>';
            return;
        }
        
        faceData.forEach(face => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${face.user_id}</td>
                <td>${face.name}</td>
                <td><img src="${face.image_url}" alt="人脸" width="50" height="50"></td>
                <td>${window.ATT.formatDateTime(face.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-danger delete-face" data-id="${face.id}">
                        删除
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // 绑定删除事件
        document.querySelectorAll('.delete-face').forEach(btn => {
            btn.addEventListener('click', function() {
                const faceId = this.getAttribute('data-id');
                self.deleteFaceData(faceId);
            });
        });
    },
    
    // 删除人脸数据
    deleteFaceData: function(faceId) {
        if (!confirm('确定要删除此人脸数据吗？')) return;
        
        axios.delete(`/api/v1/face/data/${faceId}`)
            .then(response => {
                window.ATT.showToast('人脸数据删除成功', 'success');
                this.loadFaceData();
            })
            .catch(error => {
                const errorMessage = error.response?.data?.detail || '删除失败';
                window.ATT.showToast(errorMessage, 'danger');
            });
    },
    
    // 播放提示音
    playSound: function(type) {
        let soundFile;
        
        switch(type) {
            case 'success':
                soundFile = '/static/sounds/success.mp3';
                break;
            case 'error':
                soundFile = '/static/sounds/error.mp3';
                break;
            default:
                return;
        }
        
        const audio = new Audio(soundFile);
        audio.play().catch(error => {
            console.error('播放声音失败:', error);
        });
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 如果当前页面是人脸识别相关页面，则初始化
    if (document.getElementById('face-video') || document.getElementById('face-management')) {
        FaceRecognition.init();
    }
});

// 导出全局对象
window.FR = window.FaceRecognition;