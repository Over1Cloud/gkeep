console.log('archive.js загружен');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен');
    const selectButton = document.getElementById('select-notes');
    const restoreSelectedButton = document.getElementById('restore-selected');
    const deleteSelectedButton = document.getElementById('delete-selected');
    const deleteAllButton = document.getElementById('delete-all');
    const notesContainer = document.getElementById('notes-container');
    const fixedFooter = document.querySelector('.fixed-footer');

    console.log('selectButton:', selectButton);
    console.log('restoreSelectedButton:', restoreSelectedButton);
    console.log('deleteSelectedButton:', deleteSelectedButton);
    console.log('deleteAllButton:', deleteAllButton);
    console.log('notesContainer:', notesContainer);

    if (!selectButton || !restoreSelectedButton || !deleteSelectedButton || !deleteAllButton || !notesContainer) {
        console.error('Один или несколько элементов не найдены');
        return;
    }

    let isSelectionMode = false;

    selectButton.addEventListener('click', function() {
        console.log('selectButton clicked');
        isSelectionMode = !isSelectionMode;
        notesContainer.classList.toggle('selection-mode');
        selectButton.textContent = isSelectionMode ? 'Отменить выбор' : 'Выбрать';
        updateSelectedButtons();
    });

    notesContainer.addEventListener('click', function(e) {
        console.log('notesContainer clicked');
        if (!isSelectionMode) return;
        const noteElement = e.target.closest('.note');
        if (noteElement) {
            e.preventDefault();
            e.stopPropagation();
            noteElement.classList.toggle('selected');
            updateSelectedButtons();
        }
    }, true);

    restoreSelectedButton.addEventListener('click', function() {
        console.log('restoreSelectedButton clicked');
        const selectedNotes = document.querySelectorAll('.note.selected');
        if (selectedNotes.length === 0) return;

        const noteIds = Array.from(selectedNotes).map(note => note.dataset.id);
        restoreNotes(noteIds);
    });

    deleteSelectedButton.addEventListener('click', function() {
        console.log('deleteSelectedButton clicked');
        const selectedNotes = document.querySelectorAll('.note.selected');
        if (selectedNotes.length === 0) return;

        if (confirm('Вы уверены, что хотите удалить выбранные заметки?')) {
            const noteIds = Array.from(selectedNotes).map(note => note.dataset.id);
            deleteNotes(noteIds);
        }
    });

    deleteAllButton.addEventListener('click', function() {
        console.log('deleteAllButton clicked');
        if (confirm('Вы уверены, что хотите удалить все заметки из архива?')) {
            const allNotes = document.querySelectorAll('.note');
            const noteIds = Array.from(allNotes).map(note => note.dataset.id);
            deleteNotes(noteIds);
        }
    });

    function updateSelectedButtons() {
        const selectedNotes = document.querySelectorAll('.note.selected');
        const count = selectedNotes.length;
        restoreSelectedButton.style.display = count > 0 ? 'inline-block' : 'none';
        deleteSelectedButton.style.display = count > 0 ? 'inline-block' : 'none';
        restoreSelectedButton.textContent = `Вернуть выбранные (${count})`;
        deleteSelectedButton.textContent = `Удалить выбранные (${count})`;
    }

    function restoreNotes(noteIds) {
        disableButtons();
        fetch('/restore_notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ note_ids: noteIds }),
        })
        .then(handleResponse)
        .then(data => {
            noteIds.forEach(id => removeNoteElement(id));
            updateUI();
        })
        .catch(handleError)
        .finally(enableButtons);
    }

    function deleteNotes(noteIds) {
        disableButtons();
        fetch('/delete_notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ note_ids: noteIds }),
        })
        .then(handleResponse)
        .then(data => {
            noteIds.forEach(id => removeNoteElement(id));
            updateUI();
        })
        .catch(handleError)
        .finally(enableButtons);
    }

    function handleResponse(response) {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    }

    function handleError(error) {
        console.error('Error:', error);
        alert('Произошла ошибка: ' + (error.message || 'Неизвестная ошибка'));
    }

    function removeNoteElement(id) {
        const noteElement = document.querySelector(`.note[data-id="${id}"]`);
        if (noteElement) {
            noteElement.classList.add('removing');
            setTimeout(() => noteElement.remove(), 300);
        }
    }

    function updateUI() {
        updateSelectedButtons();
        if (document.querySelectorAll('.note').length === 0) {
            notesContainer.innerHTML = '<p>Нет архивированных заметок</p>';
        }
    }

    function disableButtons() {
        [selectButton, restoreSelectedButton, deleteSelectedButton, deleteAllButton].forEach(btn => {
            if (btn) btn.disabled = true;
        });
    }

    function enableButtons() {
        [selectButton, restoreSelectedButton, deleteSelectedButton, deleteAllButton].forEach(btn => {
            if (btn) btn.disabled = false;
        });
    }

    // Новая функция для отмены выбора всех заметок
    function deselectAllNotes() {
        document.querySelectorAll('.note.selected').forEach(note => {
            note.classList.remove('selected');
        });
        updateSelectedButtons();
    }

    // Новая функция для выбора всех заметок
    function selectAllNotes() {
        document.querySelectorAll('.note').forEach(note => {
            note.classList.add('selected');
        });
        updateSelectedButtons();
    }

    // Добавьте кнопки "Выбрать все" и "Отменить выбор" в HTML и привяжите к ним эти функции
    const selectAllButton = document.getElementById('select-all');
    const deselectAllButton = document.getElementById('deselect-all');

    if (selectAllButton) {
        selectAllButton.addEventListener('click', selectAllNotes);
    }

    if (deselectAllButton) {
        deselectAllButton.addEventListener('click', deselectAllNotes);
    }
});
