const labelMapping = {
    label_1: "通过",
    label_2: "不通过",
    label_3: "图片、表格Caption混入",
    label_4: "行内公式缺失",
    label_5: "行内公式转换错误",
    label_6: "行间公式转换错误",
    label_7: "阅读顺序错误",
    label_8: "页眉、页脚、边注、footnote混入正文",
    label_9: "文本分段错误",
    label_10: "抽取内容不完整"
};

document.addEventListener('DOMContentLoaded', function() {
    const labelStats = JSON.parse(localStorage.getItem('labelStats'));
    if (labelStats) {
        renderBarChart(labelStats);
        renderPieChart(labelStats);
    } else {
        fetch('/get_label_stats').then(response => response.json()).then(data => {
            if (data.status === 'success') {
                const labelStats = data.label_stats;
                localStorage.setItem('labelStats', JSON.stringify(labelStats));
                renderBarChart(labelStats);
                renderPieChart(labelStats);
            } else {
                console.error(data.message);
            }
        }).catch(error => console.error('Error:', error));
    }
});

function renderBarChart(labelStats) {
    const labels = Object.keys(labelMapping).map(key => labelMapping[key]);
    const counts = [
        labelStats.label_1_count,
        labelStats.label_2_count,
        labelStats.label_3_count,
        labelStats.label_4_count,
        labelStats.label_5_count,
        labelStats.label_6_count,
        labelStats.label_7_count,
        labelStats.label_8_count,
        labelStats.label_9_count,
        labelStats.label_10_count
    ];

    const chartDom = document.getElementById('labelBarChart');
    const myChart = echarts.init(chartDom);
    const option = {
        title: {
            text: '标签统计',
        },
        tooltip: {},
        xAxis: {
            data: labels
        },
        yAxis: {},
        series: [{
            name: '标签数量',
            type: 'bar',
            data: counts
        }]
    };
    myChart.setOption(option);
}

function renderPieChart(labelStats) {
    const labels = Object.keys(labelMapping).map(key => labelMapping[key]);
    const counts = [
        labelStats.label_1_count,
        labelStats.label_2_count,
        labelStats.label_3_count,
        labelStats.label_4_count,
        labelStats.label_5_count,
        labelStats.label_6_count,
        labelStats.label_7_count,
        labelStats.label_8_count,
        labelStats.label_9_count,
        labelStats.label_10_count
    ];

    const total = counts.reduce((sum, count) => sum + count, 0);
    const pieData = labels.map((label, index) => ({
        name: label,
        value: counts[index]
    }));

    const chartDom = document.getElementById('labelPieChart');
    const myChart = echarts.init(chartDom);
    const option = {
        title: {
            text: '标签比例',
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b} : {c} ({d}%)'
        },
        series: [{
            name: '标签比例',
            type: 'pie',
            radius: '50%',
            data: pieData,
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    myChart.setOption(option);
}

document.getElementById('backToHomeBtn').addEventListener('click', function() {
    window.location.href = '/';
});
