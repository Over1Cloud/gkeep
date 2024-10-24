console.log('Sidebar.js loaded');
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const menuToggle = document.getElementById('menu-toggle');

    console.log('sidebar:', sidebar);
    console.log('mainContent:', mainContent);
    console.log('menuToggle:', menuToggle);

    if (!sidebar || !mainContent || !menuToggle) {
        console.error('Один или несколько элементов не найдены');
        return;
    }

    function toggleSidebar() {
        console.log('Toggling sidebar');
        sidebar.classList.toggle('open');
        mainContent.classList.toggle('shifted');
    }

    menuToggle.addEventListener('click', function(event) {
        console.log('Menu toggle clicked');
        event.stopPropagation();
        toggleSidebar();
    });

    // Закрытие сайдбара при клике вне его области
    document.addEventListener('click', function(event) {
        if (sidebar.classList.contains('open') && 
            !sidebar.contains(event.target) && 
            event.target !== menuToggle) {
            toggleSidebar();
        }
    });

    // Предотвращение закрытия сайдбара при клике внутри него
    sidebar.addEventListener('click', function(event) {
        event.stopPropagation();
    });

    // Закрытие сайдбара при изменении размера окна на мобильных устройствах
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
            toggleSidebar();
        }
    });
});
