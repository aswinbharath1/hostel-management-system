
document.addEventListener('DOMContentLoaded', function () {

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    sidebarToggle.addEventListener('click', function () {

        if (window.innerWidth <= 768) {
            // Mobile: Show or hide sidebar
            sidebar.classList.toggle('mobile-open');
        } else {
            // Desktop: Collapse or expand sidebar
            sidebar.classList.toggle('collapsed');
        }

    });

});
