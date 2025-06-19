document.addEventListener('DOMContentLoaded', () => {
    const citySelect = document.getElementById('city-select');
    const typeSelect = document.getElementById('type-select');
    const chartCanvas = document.getElementById('price-chart');
    let allData = {};
    let priceChart = null;

    // 1. 异步加载数据
    fetch('all_stats.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            allData = data;
            // 2. 动态填充城市下拉菜单
            const cities = Object.keys(data).sort();
            cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });

            // 3. 设置默认选项并初始化图表
            citySelect.value = '北京'; // 默认选中北京
            typeSelect.value = 'secondhand'; // 默认选中二手房
            updateChart();
        })
        .catch(error => console.error("无法加载房价数据:", error));

    // 4. 事件监听器
    citySelect.addEventListener('change', updateChart);
    typeSelect.addEventListener('change', updateChart);

    // 5. 更新图表的函数
    function updateChart() {
        const selectedCity = citySelect.value;
        const selectedType = typeSelect.value;
        
        if (!allData[selectedCity] || !allData[selectedCity][selectedType]) {
            console.warn(`没有找到 ${selectedCity} 的 ${selectedType} 数据`);
            if (priceChart) {
                priceChart.destroy(); // 清除旧图表
            }
            return;
        }
        
        const monthlyData = allData[selectedCity][selectedType];
        const months = Object.keys(monthlyData).sort();
        
        const labels = [];
        const chartData = [];
        let currentIndex = 100.0; // 设定基准指数为100

        // 根据环比数据计算指数
        months.forEach((month, i) => {
            labels.push(month);
            const momChange = parseFloat(monthlyData[month]);

            if (i > 0 && !isNaN(momChange)) {
                // 公式: 当月指数 = 上月指数 * 当月环比 / 100
                currentIndex = (currentIndex * momChange) / 100;
            } else if (i === 0) {
                 // 第一个数据点使用基准指数
                currentIndex = 100.0;
            }
            // 如果数据无效，则保持上一个月的指数
            chartData.push(currentIndex.toFixed(2));
        });

        // 6. 绘制图表
        if (priceChart) {
            priceChart.destroy();
        }

        priceChart = new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${selectedCity} - ${selectedType === 'new' ? '新房' : '二手房'} 价格指数 (基准=100)`,
                    data: chartData,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '价格指数'
                        }
                    },
                    x: {
                         title: {
                            display: true,
                            text: '月份'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }
}); 