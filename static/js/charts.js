/**
 * 图表相关JavaScript功能
 * 包含考勤统计图表、数据可视化等功能
 */

window.Charts = {
    // 图表实例
    chartInstances: {},
    
    // 默认图表配置
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    font: {
                        family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                    }
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                titleFont: {
                    family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                },
                bodyFont: {
                    family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                    }
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    font: {
                        family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                    }
                }
            }
        }
    },
    
    // 初始化函数
    init: function() {
        this.bindEvents();
        this.initCharts();
    },
    
    // 绑定事件
    bindEvents: function() {
        const self = this;
        
        // 时间范围选择器
        const timeRangeSelect = document.getElementById('time-range');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', function() {
                self.updateCharts();
            });
        }
        
        // 部门选择器
        const departmentSelect = document.getElementById('department-filter');
        if (departmentSelect) {
            departmentSelect.addEventListener('change', function() {
                self.updateCharts();
            });
        }
        
        // 导出图表按钮
        const exportButtons = document.querySelectorAll('.export-chart');
        exportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const chartId = this.getAttribute('data-chart');
                self.exportChart(chartId);
            });
        });
        
        // 刷新数据按钮
        const refreshButton = document.getElementById('refresh-charts');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                self.updateCharts();
            });
        }
    },
    
    // 初始化图表
    initCharts: function() {
        // 考勤趋势图
        this.initAttendanceTrendChart();
        
        // 考勤状态分布图
        this.initAttendanceStatusChart();
        
        // 部门考勤对比图
        this.initDepartmentComparisonChart();
        
        // 工作时长分布图
        this.initWorkHoursChart();
        
        // 迟到早退趋势图
        this.initLateEarlyTrendChart();
        
        // 请假类型分布图
        this.initLeaveTypeChart();
        
        // 员工出勤率排名图
        this.initAttendanceRankingChart();
    },
    
    // 初始化考勤趋势图
    initAttendanceTrendChart: function() {
        const ctx = document.getElementById('attendance-trend-chart');
        if (!ctx) return;
        
        this.chartInstances.attendanceTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '正常',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: '迟到',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: '早退',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: '缺勤',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: this.defaultOptions
        });
    },
    
    // 初始化考勤状态分布图
    initAttendanceStatusChart: function() {
        const ctx = document.getElementById('attendance-status-chart');
        if (!ctx) return;
        
        this.chartInstances.attendanceStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['正常', '迟到', '早退', '缺勤', '请假'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 205, 86, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    },
    
    // 初始化部门考勤对比图
    initDepartmentComparisonChart: function() {
        const ctx = document.getElementById('department-comparison-chart');
        if (!ctx) return;
        
        this.chartInstances.departmentComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '出勤率 (%)',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.8)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: '迟到率 (%)',
                        data: [],
                        backgroundColor: 'rgba(255, 159, 64, 0.8)',
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        max: 100
                    }
                }
            }
        });
    },
    
    // 初始化工作时长分布图
    initWorkHoursChart: function() {
        const ctx = document.getElementById('work-hours-chart');
        if (!ctx) return;
        
        this.chartInstances.workHours = new Chart(ctx, {
            type: 'histogram',
            data: {
                labels: ['<6小时', '6-7小时', '7-8小时', '8-9小时', '9-10小时', '>10小时'],
                datasets: [{
                    label: '人数',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: this.defaultOptions
        });
    },
    
    // 初始化迟到早退趋势图
    initLateEarlyTrendChart: function() {
        const ctx = document.getElementById('late-early-trend-chart');
        if (!ctx) return;
        
        this.chartInstances.lateEarlyTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '迟到次数',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: '早退次数',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: this.defaultOptions
        });
    },
    
    // 初始化请假类型分布图
    initLeaveTypeChart: function() {
        const ctx = document.getElementById('leave-type-chart');
        if (!ctx) return;
        
        this.chartInstances.leaveType = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['事假', '病假', '年假', '婚假', '产假', '丧假', '其他'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(201, 203, 207, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    },
    
    // 初始化员工出勤率排名图
    initAttendanceRankingChart: function() {
        const ctx = document.getElementById('attendance-ranking-chart');
        if (!ctx) return;
        
        this.chartInstances.attendanceRanking = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: [],
                datasets: [{
                    label: '出勤率 (%)',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        beginAtZero: false
                    },
                    x: {
                        ...this.defaultOptions.scales.x,
                        max: 100
                    }
                }
            }
        });
    },
    
    // 更新所有图表
    updateCharts: function() {
        const timeRange = document.getElementById('time-range')?.value || 'month';
        const department = document.getElementById('department-filter')?.value || 'all';
        
        // 显示加载状态
        const refreshButton = document.getElementById('refresh-charts');
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>加载中...';
        }
        
        // 获取统计数据
        axios.get('/api/v1/statistics/charts', {
            params: {
                time_range: timeRange,
                department: department
            }
        })
        .then(response => {
            const data = response.data;
            
            // 更新各个图表
            this.updateAttendanceTrendChart(data.attendance_trend);
            this.updateAttendanceStatusChart(data.attendance_status);
            this.updateDepartmentComparisonChart(data.department_comparison);
            this.updateWorkHoursChart(data.work_hours_distribution);
            this.updateLateEarlyTrendChart(data.late_early_trend);
            this.updateLeaveTypeChart(data.leave_type_distribution);
            this.updateAttendanceRankingChart(data.attendance_ranking);
            
            // 更新统计卡片
            this.updateStatisticsCards(data.summary);
        })
        .catch(error => {
            console.error('获取统计数据失败:', error);
            window.ATT.showToast('获取统计数据失败', 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            if (refreshButton) {
                refreshButton.disabled = false;
                refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>刷新数据';
            }
        });
    },
    
    // 更新考勤趋势图
    updateAttendanceTrendChart: function(data) {
        if (!this.chartInstances.attendanceTrend || !data) return;
        
        this.chartInstances.attendanceTrend.data.labels = data.labels;
        this.chartInstances.attendanceTrend.data.datasets[0].data = data.normal;
        this.chartInstances.attendanceTrend.data.datasets[1].data = data.late;
        this.chartInstances.attendanceTrend.data.datasets[2].data = data.early;
        this.chartInstances.attendanceTrend.data.datasets[3].data = data.absent;
        
        this.chartInstances.attendanceTrend.update();
    },
    
    // 更新考勤状态分布图
    updateAttendanceStatusChart: function(data) {
        if (!this.chartInstances.attendanceStatus || !data) return;
        
        this.chartInstances.attendanceStatus.data.datasets[0].data = data;
        
        this.chartInstances.attendanceStatus.update();
    },
    
    // 更新部门考勤对比图
    updateDepartmentComparisonChart: function(data) {
        if (!this.chartInstances.departmentComparison || !data) return;
        
        this.chartInstances.departmentComparison.data.labels = data.departments;
        this.chartInstances.departmentComparison.data.datasets[0].data = data.attendance_rates;
        this.chartInstances.departmentComparison.data.datasets[1].data = data.late_rates;
        
        this.chartInstances.departmentComparison.update();
    },
    
    // 更新工作时长分布图
    updateWorkHoursChart: function(data) {
        if (!this.chartInstances.workHours || !data) return;
        
        this.chartInstances.workHours.data.datasets[0].data = data;
        
        this.chartInstances.workHours.update();
    },
    
    // 更新迟到早退趋势图
    updateLateEarlyTrendChart: function(data) {
        if (!this.chartInstances.lateEarlyTrend || !data) return;
        
        this.chartInstances.lateEarlyTrend.data.labels = data.labels;
        this.chartInstances.lateEarlyTrend.data.datasets[0].data = data.late;
        this.chartInstances.lateEarlyTrend.data.datasets[1].data = data.early;
        
        this.chartInstances.lateEarlyTrend.update();
    },
    
    // 更新请假类型分布图
    updateLeaveTypeChart: function(data) {
        if (!this.chartInstances.leaveType || !data) return;
        
        this.chartInstances.leaveType.data.datasets[0].data = data;
        
        this.chartInstances.leaveType.update();
    },
    
    // 更新员工出勤率排名图
    updateAttendanceRankingChart: function(data) {
        if (!this.chartInstances.attendanceRanking || !data) return;
        
        this.chartInstances.attendanceRanking.data.labels = data.names;
        this.chartInstances.attendanceRanking.data.datasets[0].data = data.rates;
        
        this.chartInstances.attendanceRanking.update();
    },
    
    // 更新统计卡片
    updateStatisticsCards: function(data) {
        if (!data) return;
        
        // 总人数
        const totalEmployeesEl = document.getElementById('total-employees');
        if (totalEmployeesEl) {
            totalEmployeesEl.textContent = data.total_employees || 0;
        }
        
        // 平均出勤率
        const avgAttendanceRateEl = document.getElementById('avg-attendance-rate');
        if (avgAttendanceRateEl) {
            avgAttendanceRateEl.textContent = (data.avg_attendance_rate || 0) + '%';
        }
        
        // 平均工作时长
        const avgWorkHoursEl = document.getElementById('avg-work-hours');
        if (avgWorkHoursEl) {
            avgWorkHoursEl.textContent = (data.avg_work_hours || 0) + '小时';
        }
        
        // 本月请假人数
        const leaveCountEl = document.getElementById('leave-count');
        if (leaveCountEl) {
            leaveCountEl.textContent = data.leave_count || 0;
        }
    },
    
    // 导出图表
    exportChart: function(chartId) {
        if (!this.chartInstances[chartId]) {
            window.ATT.showToast('图表不存在', 'warning');
            return;
        }
        
        const chart = this.chartInstances[chartId];
        const url = chart.toBase64Image();
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.download = `${chartId}-${new Date().toISOString().slice(0, 10)}.png`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.ATT.showToast('图表导出成功', 'success');
    },
    
    // 销毁所有图表
    destroyCharts: function() {
        Object.keys(this.chartInstances).forEach(key => {
            if (this.chartInstances[key]) {
                this.chartInstances[key].destroy();
                delete this.chartInstances[key];
            }
        });
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 如果当前页面包含图表元素，则初始化
    if (document.querySelector('[id$="-chart"]')) {
        Charts.init();
    }
});

// 导出全局对象
window.CHARTS = window.Charts;