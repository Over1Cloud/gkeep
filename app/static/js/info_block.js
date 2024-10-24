document.addEventListener('DOMContentLoaded', function() {
    const normHoursInput = document.getElementById('norm-hours');
    const totalHoursSpan = document.getElementById('total-hours');
    const nightHoursSpan = document.getElementById('night-hours');
    const salarySpan = document.getElementById('salary');
    const advanceSpan = document.getElementById('advance');

    const monthSelect = document.querySelector('.month-select');
    const yearSelect = document.querySelector('.year-select');

    // Проверяем, существуют ли элементы выбора месяца и года
    if (!monthSelect || !yearSelect) {
        console.error('Элементы выбора месяца и/или года не найдены');
        return; // Прекращаем выполнение скрипта, если элементы не найдены
    }

    let currentDate = moment().tz('Europe/Moscow');

    const months = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Дебрь'
    ];

    function updateSelects() {
        monthSelect.innerHTML = months.map((month, index) => 
            `<option value="${index}" ${currentDate.month() === index ? 'selected' : ''}>${month}</option>`
        ).join('');

        const currentYear = moment().year();
        yearSelect.innerHTML = Array.from({length: 10}, (_, i) => currentYear - 5 + i).map(year => 
            `<option value="${year}" ${currentDate.year() === year ? 'selected' : ''}>${year}</option>`
        ).join('');
    }

    function loadInfo() {
        const dateStr = currentDate.format('MM.YYYY');
        fetch(`/get_info/${dateStr}`)
            .then(response => response.json())
            .then(data => {
                if (normHoursInput) normHoursInput.value = data.norm_hours || '';
                if (totalHoursSpan) totalHoursSpan.textContent = `Всего отработано: ${data.total_hours || 0}`;
                if (nightHoursSpan) nightHoursSpan.textContent = `Ночные часы: ${data.night_hours || 0}`;
                if (salarySpan) salarySpan.textContent = `Зарплата: ${data.salary || 0}`;
                if (advanceSpan) advanceSpan.textContent = `Аванс: ${data.advance || 0}`;
                sortNotes(dateStr);
            })
            .catch(error => console.error('Error:', error));
    }

    function saveInfo() {
        if (!normHoursInput) return;

        const data = {
            month_year: currentDate.format('MM.YYYY'),
            norm_hours: normHoursInput.value
        };

        fetch('/save_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Информация сохранена успешно');
                loadInfo();
            } else {
                console.error('Ошибка при сохранении информации');
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function sortNotes(dateStr) {
        const notesContainer = document.getElementById('notes-container');
        if (!notesContainer) return;

        const notes = Array.from(notesContainer.getElementsByClassName('note'));
        
        notes.sort((a, b) => {
            const dateA = moment(a.dataset.date, 'DD.MM.YYYY');
            const dateB = moment(b.dataset.date, 'DD.MM.YYYY');
            return dateB - dateA;
        });

        const [month, year] = dateStr.split('.');
        notes.forEach(note => {
            const noteDate = moment(note.dataset.date, 'DD.MM.YYYY');
            if (noteDate.format('MM.YYYY') === dateStr) {
                note.style.display = 'block';
            } else {
                note.style.display = 'none';
            }
        });

        notesContainer.innerHTML = '';
        notes.forEach(note => notesContainer.appendChild(note));
    }

    const selectNotesButton = document.getElementById('select-notes');
    const archiveSelectedButton = document.getElementById('archive-selected');
    const deleteSelectedButton = document.getElementById('delete-selected');
    const notesContainer = document.getElementById('notes-container');
    let isSelectMode = false;

    if (selectNotesButton) {
        selectNotesButton.addEventListener('click', toggleSelectMode);
    }

    function toggleSelectMode() {
        isSelectMode = !isSelectMode;
        document.body.classList.toggle('selection-mode', isSelectMode);
        const notes = document.querySelectorAll('.note');
        notes.forEach(note => {
            note.classList.toggle('selectable', isSelectMode);
            if (!isSelectMode) {
                note.classList.remove('selected');
            }
        });
        updateSelectedCount();
        selectNotesButton.textContent = isSelectMode ? 'Отменить выбор' : 'Выбрать';
    }

    if (notesContainer) {
        notesContainer.addEventListener('click', function(event) {
            if (!isSelectMode) return;
            const note = event.target.closest('.note');
            if (note) {
                event.preventDefault();
                event.stopPropagation();
                note.classList.toggle('selected');
                updateSelectedCount();
            }
        });
    }

    function updateSelectedCount() {
        const selectedCount = document.querySelectorAll('.note.selected').length;
        if (archiveSelectedButton) {
            archiveSelectedButton.style.display = selectedCount > 0 ? 'inline-block' : 'none';
            archiveSelectedButton.textContent = `В архив (${selectedCount})`;
        }
        if (deleteSelectedButton) {
            deleteSelectedButton.style.display = selectedCount > 0 ? 'inline-block' : 'none';
            deleteSelectedButton.textContent = `Удалить (${selectedCount})`;
        }
    }

    updateSelects();
    loadInfo();

    monthSelect.addEventListener('change', function() {
        currentDate.month(this.value);
        loadInfo();
    });

    yearSelect.addEventListener('change', function() {
        currentDate.year(this.value);
        loadInfo();
    });

    if (normHoursInput) {
        normHoursInput.addEventListener('change', saveInfo);
    }

    // Вызовите эту функцию при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        updateSelectedCount();
    });
});
