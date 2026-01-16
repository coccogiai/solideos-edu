"""
PDF 리포트 생성 모듈
5분간 수집된 시스템 리소스 데이터를 PDF 리포트로 생성합니다.
"""

import os
import io
from datetime import datetime
from typing import List, Dict, Any

import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드 사용
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class PDFReportGenerator:
    """시스템 모니터링 PDF 리포트 생성기"""
    
    def __init__(self, data: List[Dict[str, Any]], output_path: str):
        self.data = data
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """커스텀 스타일 설정"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a1a2e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#16213e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5
        ))
    
    def _create_chart(self, title: str, timestamps: List[str], 
                      data_series: Dict[str, List[float]], 
                      ylabel: str, figsize=(8, 3)) -> io.BytesIO:
        """시계열 차트 생성"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # 색상 팔레트
        colors_palette = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        
        x_values = range(len(timestamps))
        
        for idx, (label, values) in enumerate(data_series.items()):
            color = colors_palette[idx % len(colors_palette)]
            ax.plot(x_values, values, label=label, linewidth=2, color=color, marker='o', markersize=2)
        
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('Time (seconds)', fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
        
        # x축 레이블 간소화
        step = max(1, len(x_values) // 10)
        ax.set_xticks(x_values[::step])
        ax.set_xticklabels([str(i) for i in x_values[::step]], fontsize=8)
        
        plt.tight_layout()
        
        # 이미지를 바이트로 저장
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """통계 계산"""
        if not values:
            return {"min": 0, "max": 0, "avg": 0}
        
        return {
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "avg": round(sum(values) / len(values), 2)
        }
    
    def _create_summary_table(self, title: str, data: List[List[str]]) -> Table:
        """요약 테이블 생성"""
        table = Table(data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        return table
    
    def generate(self):
        """PDF 리포트 생성"""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # 타이틀
        elements.append(Paragraph("시스템 리소스 모니터링 리포트", self.styles['CustomTitle']))
        elements.append(Paragraph(
            f"실시간 시스템 성능 분석 보고서",
            ParagraphStyle(name='SubTitle', parent=self.styles['Normal'], 
                          fontSize=12, alignment=TA_CENTER, textColor=colors.gray)
        ))
        elements.append(Spacer(1, 20))
        
        # 리포트 정보
        if self.data:
            start_time = self.data[0].get('timestamp', '정보 없음')
            end_time = self.data[-1].get('timestamp', '정보 없음')
            duration = len(self.data)
        else:
            start_time = end_time = '정보 없음'
            duration = 0
        
        info_data = [
            ['리포트 정보', '', '', ''],
            ['시작 시간', start_time, '종료 시간', end_time],
            ['추적 시간', f'{duration} 초', '데이터 포인트', str(len(self.data))]
        ]
        info_table = self._create_summary_table("정보", info_data)
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # 데이터 추출
        timestamps = [d.get('timestamp', '') for d in self.data]
        cpu_usage = [d.get('cpu', {}).get('usage_percent', 0) for d in self.data]
        cpu_temps = [d.get('cpu', {}).get('temperature') or 0 for d in self.data]
        mem_usage = [d.get('memory', {}).get('usage_percent', 0) for d in self.data]
        mem_used = [d.get('memory', {}).get('used_gb', 0) for d in self.data]
        net_up = [d.get('network', {}).get('upload_speed_kbps', 0) for d in self.data]
        net_down = [d.get('network', {}).get('download_speed_kbps', 0) for d in self.data]
        disk_read = [d.get('disk', {}).get('io_read_speed_mbps', 0) for d in self.data]
        disk_write = [d.get('disk', {}).get('io_write_speed_mbps', 0) for d in self.data]
        
        # GPU 데이터
        gpu_usage = []
        gpu_temps = []
        gpu_mem = []
        for d in self.data:
            gpus = d.get('gpu', [])
            if gpus:
                gpu_usage.append(gpus[0].get('load_percent', 0))
                gpu_temps.append(gpus[0].get('temperature') or 0)
                gpu_mem.append(gpus[0].get('memory_percent', 0))
            else:
                gpu_usage.append(0)
                gpu_temps.append(0)
                gpu_mem.append(0)
        
        # === CPU 섹션 ===
        elements.append(Paragraph("CPU 모니터링", self.styles['SectionTitle']))
        
        # CPU 차트
        cpu_chart = self._create_chart(
            "CPU 사용률 추이",
            timestamps,
            {"CPU 사용률 (%)": cpu_usage},
            "사용률 (%)"
        )
        elements.append(Image(cpu_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 10))
        
        # CPU 통계
        cpu_stats = self._calculate_statistics(cpu_usage)
        temp_stats = self._calculate_statistics([t for t in cpu_temps if t > 0])
        cpu_table_data = [
            ['항목', '최소', '최대', '평균'],
            ['CPU 사용률 (%)', str(cpu_stats['min']), str(cpu_stats['max']), str(cpu_stats['avg'])],
            ['온도 (°C)', str(temp_stats['min']), str(temp_stats['max']), str(temp_stats['avg'])]
        ]
        elements.append(self._create_summary_table("CPU 통계", cpu_table_data))
        elements.append(Spacer(1, 20))
        
        # === Memory 섹션 ===
        elements.append(Paragraph("메모리 모니터링", self.styles['SectionTitle']))
        
        mem_chart = self._create_chart(
            "메모리 사용 추이",
            timestamps,
            {"메모리 사용률 (%)": mem_usage, "사용량 (GB)": mem_used},
            "값"
        )
        elements.append(Image(mem_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 10))
        
        mem_stats = self._calculate_statistics(mem_usage)
        used_stats = self._calculate_statistics(mem_used)
        mem_table_data = [
            ['항목', '최소', '최대', '평균'],
            ['메모리 사용률 (%)', str(mem_stats['min']), str(mem_stats['max']), str(mem_stats['avg'])],
            ['사용량 (GB)', str(used_stats['min']), str(used_stats['max']), str(used_stats['avg'])]
        ]
        elements.append(self._create_summary_table("메모리 통계", mem_table_data))
        
        elements.append(PageBreak())
        
        # === Network 섹션 ===
        elements.append(Paragraph("네트워크 트래픽", self.styles['SectionTitle']))
        
        net_chart = self._create_chart(
            "네트워크 속도 추이",
            timestamps,
            {"업로드 (Kbps)": net_up, "다운로드 (Kbps)": net_down},
            "속도 (Kbps)"
        )
        elements.append(Image(net_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 10))
        
        up_stats = self._calculate_statistics(net_up)
        down_stats = self._calculate_statistics(net_down)
        net_table_data = [
            ['항목', '최소', '최대', '평균'],
            ['업로드 (Kbps)', str(up_stats['min']), str(up_stats['max']), str(up_stats['avg'])],
            ['다운로드 (Kbps)', str(down_stats['min']), str(down_stats['max']), str(down_stats['avg'])]
        ]
        elements.append(self._create_summary_table("네트워크 통계", net_table_data))
        elements.append(Spacer(1, 20))
        
        # === Disk I/O 섹션 ===
        elements.append(Paragraph("디스크 입출력", self.styles['SectionTitle']))
        
        disk_chart = self._create_chart(
            "디스크 I/O 추이",
            timestamps,
            {"읽기 (MB/s)": disk_read, "쓰기 (MB/s)": disk_write},
            "속도 (MB/s)"
        )
        elements.append(Image(disk_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 10))
        
        read_stats = self._calculate_statistics(disk_read)
        write_stats = self._calculate_statistics(disk_write)
        disk_table_data = [
            ['항목', '최소', '최대', '평균'],
            ['읽기 속도 (MB/s)', str(read_stats['min']), str(read_stats['max']), str(read_stats['avg'])],
            ['쓰기 속도 (MB/s)', str(write_stats['min']), str(write_stats['max']), str(write_stats['avg'])]
        ]
        elements.append(self._create_summary_table("디스크 통계", disk_table_data))
        elements.append(Spacer(1, 20))
        
        # === GPU 섹션 ===
        if any(g > 0 for g in gpu_usage):
            elements.append(Paragraph("GPU 모니터링", self.styles['SectionTitle']))
            
            gpu_chart = self._create_chart(
                "GPU 사용률 추이",
                timestamps,
                {"GPU 부하 (%)": gpu_usage, "GPU 메모리 (%)": gpu_mem},
                "사용률 (%)"
            )
            elements.append(Image(gpu_chart, width=16*cm, height=6*cm))
            elements.append(Spacer(1, 10))
            
            gpu_stats = self._calculate_statistics(gpu_usage)
            gpu_temp_stats = self._calculate_statistics([t for t in gpu_temps if t > 0])
            gpu_mem_stats = self._calculate_statistics(gpu_mem)
            gpu_table_data = [
                ['항목', '최소', '최대', '평균'],
                ['GPU 부하 (%)', str(gpu_stats['min']), str(gpu_stats['max']), str(gpu_stats['avg'])],
                ['GPU 온도 (°C)', str(gpu_temp_stats['min']), str(gpu_temp_stats['max']), str(gpu_temp_stats['avg'])],
                ['GPU 메모리 (%)', str(gpu_mem_stats['min']), str(gpu_mem_stats['max']), str(gpu_mem_stats['avg'])]
            ]
            elements.append(self._create_summary_table("GPU 통계", gpu_table_data))
        
        # 푸터
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"생성 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}",
            ParagraphStyle(name='Footer', parent=self.styles['Normal'], 
                          fontSize=8, alignment=TA_CENTER, textColor=colors.gray)
        ))
        
        # PDF 빌드
        doc.build(elements)
        return self.output_path


# 테스트용
if __name__ == "__main__":
    # 샘플 데이터 생성
    import random
    
    sample_data = []
    for i in range(60):
        sample_data.append({
            "timestamp": f"2024-01-16 10:{i//60:02d}:{i%60:02d}",
            "cpu": {"usage_percent": random.uniform(20, 80), "temperature": random.uniform(40, 70)},
            "memory": {"usage_percent": random.uniform(50, 80), "used_gb": random.uniform(8, 12)},
            "network": {"upload_speed_kbps": random.uniform(100, 1000), "download_speed_kbps": random.uniform(500, 5000)},
            "disk": {"io_read_speed_mbps": random.uniform(0, 100), "io_write_speed_mbps": random.uniform(0, 50)},
            "gpu": [{"load_percent": random.uniform(0, 50), "temperature": random.uniform(40, 60), "memory_percent": random.uniform(20, 40)}]
        })
    
    generator = PDFReportGenerator(sample_data, "test_report.pdf")
    generator.generate()
    print("PDF generated: test_report.pdf")
