/**
 * System Monitor Dashboard JavaScript
 * 실시간 시스템 리소스 모니터링 및 차트 업데이트
 */

// Socket.IO 연결
const socket = io();

// 차트 인스턴스
let cpuChart, memoryChart, gpuChart, networkChart, diskChart, cpuGauge;

// 차트 데이터 히스토리 (최대 60개 포인트)
const MAX_DATA_POINTS = 60;
const chartData = {
    cpu: [],
    memory: [],
    gpu: [],
    networkUp: [],
    networkDown: [],
    diskRead: [],
    diskWrite: [],
    labels: []
};

// 차트 공통 옵션
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 300
    },
    plugins: {
        legend: {
            display: false
        }
    },
    scales: {
        x: {
            display: false
        },
        y: {
            display: true,
            min: 0,
            grid: {
                color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
                color: 'rgba(255, 255, 255, 0.5)',
                font: {
                    size: 10
                }
            }
        }
    },
    elements: {
        point: {
            radius: 0
        },
        line: {
            tension: 0.4,
            borderWidth: 2
        }
    }
};

// 차트 초기화
function initCharts() {
    // CPU 차트
    const cpuCtx = document.getElementById('cpuChart').getContext('2d');
    cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true
            }]
        },
        options: {
            ...commonChartOptions,
            scales: {
                ...commonChartOptions.scales,
                y: { ...commonChartOptions.scales.y, max: 100 }
            }
        }
    });

    // CPU 게이지
    const gaugeCtx = document.getElementById('cpuGauge').getContext('2d');
    cpuGauge = new Chart(gaugeCtx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(255, 255, 255, 0.1)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '75%',
            rotation: -90,
            circumference: 180,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });

    // 메모리 차트
    const memCtx = document.getElementById('memoryChart').getContext('2d');
    memoryChart = new Chart(memCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#4facfe',
                backgroundColor: 'rgba(79, 172, 254, 0.1)',
                fill: true
            }]
        },
        options: {
            ...commonChartOptions,
            scales: {
                ...commonChartOptions.scales,
                y: { ...commonChartOptions.scales.y, max: 100 }
            }
        }
    });

    // GPU 차트
    const gpuCtx = document.getElementById('gpuChart').getContext('2d');
    gpuChart = new Chart(gpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#f093fb',
                backgroundColor: 'rgba(240, 147, 251, 0.1)',
                fill: true
            }]
        },
        options: {
            ...commonChartOptions,
            scales: {
                ...commonChartOptions.scales,
                y: { ...commonChartOptions.scales.y, max: 100 }
            }
        }
    });

    // 네트워크 차트
    const netCtx = document.getElementById('networkChart').getContext('2d');
    networkChart = new Chart(netCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upload',
                    data: [],
                    borderColor: '#4facfe',
                    backgroundColor: 'rgba(79, 172, 254, 0.1)',
                    fill: true
                },
                {
                    label: 'Download',
                    data: [],
                    borderColor: '#00f2fe',
                    backgroundColor: 'rgba(0, 242, 254, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            ...commonChartOptions,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: { size: 10 },
                        boxWidth: 15
                    }
                }
            }
        }
    });

    // 디스크 차트
    const diskCtx = document.getElementById('diskChart').getContext('2d');
    diskChart = new Chart(diskCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Read',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true
                },
                {
                    label: 'Write',
                    data: [],
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            ...commonChartOptions,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: { size: 10 },
                        boxWidth: 15
                    }
                }
            }
        }
    });
}

// 차트 데이터 업데이트
function updateChartData(stats) {
    const now = new Date().toLocaleTimeString();
    
    // 데이터 추가
    chartData.labels.push(now);
    chartData.cpu.push(stats.cpu?.usage_percent || 0);
    chartData.memory.push(stats.memory?.usage_percent || 0);
    chartData.gpu.push(stats.gpu?.[0]?.load_percent || 0);
    chartData.networkUp.push(stats.network?.upload_speed_kbps || 0);
    chartData.networkDown.push(stats.network?.download_speed_kbps || 0);
    chartData.diskRead.push(stats.disk?.io_read_speed_mbps || 0);
    chartData.diskWrite.push(stats.disk?.io_write_speed_mbps || 0);
    
    // 최대 개수 유지
    if (chartData.labels.length > MAX_DATA_POINTS) {
        chartData.labels.shift();
        chartData.cpu.shift();
        chartData.memory.shift();
        chartData.gpu.shift();
        chartData.networkUp.shift();
        chartData.networkDown.shift();
        chartData.diskRead.shift();
        chartData.diskWrite.shift();
    }
    
    // 차트 업데이트
    cpuChart.data.labels = chartData.labels;
    cpuChart.data.datasets[0].data = chartData.cpu;
    cpuChart.update('none');
    
    memoryChart.data.labels = chartData.labels;
    memoryChart.data.datasets[0].data = chartData.memory;
    memoryChart.update('none');
    
    gpuChart.data.labels = chartData.labels;
    gpuChart.data.datasets[0].data = chartData.gpu;
    gpuChart.update('none');
    
    networkChart.data.labels = chartData.labels;
    networkChart.data.datasets[0].data = chartData.networkUp;
    networkChart.data.datasets[1].data = chartData.networkDown;
    networkChart.update('none');
    
    diskChart.data.labels = chartData.labels;
    diskChart.data.datasets[0].data = chartData.diskRead;
    diskChart.data.datasets[1].data = chartData.diskWrite;
    diskChart.update('none');
    
    // CPU 게이지 업데이트
    const cpuUsage = stats.cpu?.usage_percent || 0;
    cpuGauge.data.datasets[0].data = [cpuUsage, 100 - cpuUsage];
    
    // 색상 변경 (사용률에 따라)
    if (cpuUsage > 80) {
        cpuGauge.data.datasets[0].backgroundColor[0] = 'rgba(245, 87, 108, 0.8)';
    } else if (cpuUsage > 60) {
        cpuGauge.data.datasets[0].backgroundColor[0] = 'rgba(250, 140, 68, 0.8)';
    } else {
        cpuGauge.data.datasets[0].backgroundColor[0] = 'rgba(102, 126, 234, 0.8)';
    }
    cpuGauge.update('none');
}

// UI 업데이트
function updateUI(stats) {
    // CPU
    const cpuUsage = stats.cpu?.usage_percent || 0;
    document.getElementById('cpuUsage').textContent = `${cpuUsage.toFixed(1)}%`;
    document.getElementById('cpuGaugeValue').textContent = cpuUsage.toFixed(0);
    document.getElementById('cpuTemp').textContent = stats.cpu?.temperature 
        ? `${stats.cpu.temperature.toFixed(0)}°C` : '--°C';
    document.getElementById('cpuFreq').textContent = stats.cpu?.frequency_current 
        ? `${stats.cpu.frequency_current.toFixed(0)} MHz` : '-- MHz';
    document.getElementById('cpuCores').textContent = stats.cpu?.core_count_logical || '--';
    
    // Memory
    const memUsage = stats.memory?.usage_percent || 0;
    document.getElementById('memUsage').textContent = `${memUsage.toFixed(1)}%`;
    document.getElementById('memoryFill').style.width = `${memUsage}%`;
    document.getElementById('memUsed').textContent = `${stats.memory?.used_gb || 0} GB`;
    document.getElementById('memTotal').textContent = `${stats.memory?.total_gb || 0} GB`;
    document.getElementById('memAvailable').textContent = `${stats.memory?.available_gb || 0} GB`;
    document.getElementById('memSwap').textContent = `${stats.memory?.swap_percent || 0}%`;
    
    // GPU
    if (stats.gpu && stats.gpu.length > 0) {
        const gpu = stats.gpu[0];
        document.getElementById('gpuUsage').textContent = `${gpu.load_percent?.toFixed(1) || 0}%`;
        document.getElementById('gpuName').textContent = gpu.name || 'Unknown GPU';
        document.getElementById('gpuTemp').textContent = gpu.temperature 
            ? `${gpu.temperature}°C` : '--°C';
        document.getElementById('gpuMemory').textContent = `${gpu.memory_used_mb?.toFixed(0) || 0} MB`;
        document.getElementById('gpuMemPercent').textContent = `${gpu.memory_percent?.toFixed(1) || 0}%`;
    } else {
        document.getElementById('gpuUsage').textContent = 'N/A';
        document.getElementById('gpuName').textContent = 'GPU를 찾을 수 없음';
    }
    
    // Network
    document.getElementById('netUpload').textContent = 
        formatSpeed(stats.network?.upload_speed_kbps || 0);
    document.getElementById('netDownload').textContent = 
        formatSpeed(stats.network?.download_speed_kbps || 0);
    document.getElementById('netTotalSent').textContent = `${stats.network?.total_sent_gb || 0} GB`;
    document.getElementById('netTotalRecv').textContent = `${stats.network?.total_recv_gb || 0} GB`;
    
    // Disk
    updateDiskPartitions(stats.disk?.partitions || []);
    document.getElementById('diskRead').textContent = `${stats.disk?.io_read_speed_mbps || 0} MB/s`;
    document.getElementById('diskWrite').textContent = `${stats.disk?.io_write_speed_mbps || 0} MB/s`;
    
    // Process
    updateProcessTable(stats.processes || []);
    
    // System
    document.getElementById('systemUptime').textContent = 
        `Uptime: ${stats.system?.uptime_hours || 0}시간`;
    
    // Tracking status
    if (stats.tracking) {
        updateTrackingUI(stats.tracking);
    }
}

// 디스크 파티션 업데이트
function updateDiskPartitions(partitions) {
    const container = document.getElementById('diskPartitions');
    container.innerHTML = '';
    
    partitions.forEach(partition => {
        const div = document.createElement('div');
        div.className = 'disk-partition';
        
        let fillClass = '';
        if (partition.usage_percent > 90) {
            fillClass = 'danger';
        } else if (partition.usage_percent > 70) {
            fillClass = 'warning';
        }
        
        div.innerHTML = `
            <span class="partition-name">${partition.device.replace(/\\\\/g, '')}</span>
            <div class="partition-bar">
                <div class="partition-fill ${fillClass}" style="width: ${partition.usage_percent}%"></div>
            </div>
            <span class="partition-info">${partition.used_gb}/${partition.total_gb} GB</span>
        `;
        
        container.appendChild(div);
    });
}

// 프로세스 테이블 업데이트
function updateProcessTable(processes) {
    const tbody = document.getElementById('processTableBody');
    tbody.innerHTML = '';
    
    processes.forEach(proc => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${proc.name}</td>
            <td>${proc.cpu_percent.toFixed(1)}%</td>
            <td>${proc.memory_percent.toFixed(1)}%</td>
        `;
        tbody.appendChild(tr);
    });
}

// 추적 UI 업데이트
function updateTrackingUI(tracking) {
    const statusEl = document.getElementById('trackingStatus');
    const progressContainer = document.getElementById('trackingProgressContainer');
    const startBtn = document.getElementById('startTrackingBtn');
    const stopBtn = document.getElementById('stopTrackingBtn');
    const pdfBtn = document.getElementById('generatePdfBtn');
    
    if (tracking.is_tracking) {
        statusEl.innerHTML = '<span class="tracking-icon">🔴</span><span class="tracking-text">추적 중...</span>';
        statusEl.classList.add('active');
        progressContainer.style.display = 'flex';
        
        document.getElementById('progressFill').style.width = `${tracking.progress}%`;
        document.getElementById('dataPoints').textContent = tracking.data_points;
        
        startBtn.disabled = true;
        stopBtn.disabled = false;
        pdfBtn.disabled = true;
    } else {
        statusEl.innerHTML = '<span class="tracking-icon">⏱️</span><span class="tracking-text">대기 중</span>';
        statusEl.classList.remove('active');
        
        if (tracking.data_points > 0) {
            progressContainer.style.display = 'flex';
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('dataPoints').textContent = tracking.data_points;
            pdfBtn.disabled = false;
        } else {
            progressContainer.style.display = 'none';
            pdfBtn.disabled = true;
        }
        
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// 속도 포맷팅
function formatSpeed(kbps) {
    if (kbps >= 1000) {
        return `${(kbps / 1000).toFixed(2)} Mbps`;
    }
    return `${kbps.toFixed(2)} Kbps`;
}

// 시간 업데이트
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString('ko-KR');
}

// Toast 알림
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 추적 시작
async function startTracking() {
    try {
        const response = await fetch('/api/start-tracking', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'started') {
            showToast('5분 추적을 시작합니다.', 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('추적 시작 실패: ' + error.message, 'error');
    }
}

// 추적 중지
async function stopTracking() {
    try {
        const response = await fetch('/api/stop-tracking', { method: 'POST' });
        const data = await response.json();
        showToast(data.message, 'info');
    } catch (error) {
        showToast('추적 중지 실패: ' + error.message, 'error');
    }
}

// PDF 생성
async function generatePDF() {
    const btn = document.getElementById('generatePdfBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> 생성 중...';
    
    try {
        const response = await fetch('/api/generate-pdf', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('PDF가 생성되었습니다. 다운로드를 시작합니다.', 'success');
            
            // PDF 다운로드
            const link = document.createElement('a');
            link.href = `/api/download-pdf/${data.filename}`;
            link.download = data.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('PDF 생성 실패: ' + error.message, 'error');
    } finally {
        btn.innerHTML = '<span class="btn-icon">📄</span> PDF 생성';
        btn.disabled = false;
    }
}

// Socket.IO 이벤트 핸들러
socket.on('connect', () => {
    console.log('Connected to server');
    const statusEl = document.getElementById('connectionStatus');
    statusEl.querySelector('.status-dot').classList.add('connected');
    statusEl.querySelector('.status-text').textContent = '연결됨';
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    const statusEl = document.getElementById('connectionStatus');
    statusEl.querySelector('.status-dot').classList.remove('connected');
    statusEl.querySelector('.status-dot').classList.add('disconnected');
    statusEl.querySelector('.status-text').textContent = '연결 끊김';
});

socket.on('stats_update', (stats) => {
    updateUI(stats);
    updateChartData(stats);
});

socket.on('tracking_complete', (data) => {
    showToast(data.message, 'success');
    document.getElementById('generatePdfBtn').disabled = false;
});

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateTime();
    setInterval(updateTime, 1000);
    
    // 초기 상태 확인
    fetch('/api/tracking-status')
        .then(res => res.json())
        .then(data => updateTrackingUI(data))
        .catch(err => console.error('Error fetching tracking status:', err));
});
