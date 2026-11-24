document.addEventListener('DOMContentLoaded', function () {

    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {

            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('mobile-open');
            } else {
                sidebar.classList.toggle('collapsed');
            }

        });
    }


    // Bed Occupancy Chart
    const chartElement = document.getElementById('bed-occupancy-chart');
    const chartDataElement = document.getElementById('bed-occupancy-data');

    if (chartElement && chartDataElement && typeof ApexCharts !== 'undefined') {

        const chartData = JSON.parse(chartDataElement.textContent);

        const rootStyles = getComputedStyle(document.documentElement);

        const primaryColor = rootStyles.getPropertyValue('--slate-blue').trim() || '#505081';
        const secondaryColor = rootStyles.getPropertyValue('--cool-gray').trim() || '#8686AC';

        const options = {
            series: chartData.series,

            chart: {
                type: 'donut',
                height: 320,
                fontFamily: 'Arial, sans-serif'
            },

            labels: chartData.labels,

            colors: [primaryColor, secondaryColor],

            legend: {
                position: 'bottom'
            },

            dataLabels: {
                enabled: true,
                formatter: function (value) {
                    return value.toFixed(1) + '%';
                }
            },

            plotOptions: {
                pie: {
                    donut: {
                        size: '65%',
                        labels: {
                            show: true,
                            total: {
                                show: true,
                                label: 'Total Beds',
                                formatter: function (w) {
                                    return w.globals.seriesTotals.reduce(
                                        (a, b) => a + b, 0
                                    );
                                }
                            }
                        }
                    }
                }
            },

            noData: {
                text: 'No bed records available'
            },

            responsive: [{
                breakpoint: 480,
                options: {
                    chart: {
                        height: 280
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }]
        };

        const chart = new ApexCharts(chartElement, options);
        chart.render();
    }

});
// Resident Categories Chart
const categoryElement = document.getElementById('resident-category-chart');
const categoryDataElement = document.getElementById('resident-category-data');

if (categoryElement && categoryDataElement && typeof ApexCharts !== 'undefined') {

    const categoryData = JSON.parse(categoryDataElement.textContent);

    const categoryChart = new ApexCharts(categoryElement, {
        series: categoryData.series,

        chart: {
            type: 'pie',
            height: 320
        },

        labels: categoryData.labels,

        colors: [
            '#272757', '#505081', '#8686AC',
            '#6366F1', '#A5B4FC', '#818CF8',
            '#4F46E5', '#C7D2FE', '#3730A3'
        ],

        legend: {
            position: 'bottom'
        },

        dataLabels: {
            enabled: true
        },

        noData: {
            text: 'No resident category data available'
        }
    });

    categoryChart.render();
}