document.addEventListener('DOMContentLoaded', function() {
    const selectNotesButton = document.getElementById('select-notes');
    const restoreSelectedButton = document.getElementById('restore-selected');
    const deleteSelectedButton = document.getElementById('delete-selected');
    const deleteAllButton = document.getElementById('delete-all');
    const notesContainer = document.getElementById('notes-container');
    let isSelectMode = false;

    if (selectNotesButton) {
        selectNotesButton.addEventListener('click', toggleSelectMode);
    }

    function toggleSelectMode() {
        isSelectMode = !isSelectMode;
        document.body.classList.toggle('selection-mode', isSelectMode);
        updateNotesSelectable();
        updateButtonsVisibility();
    }

    function updateNotesSelectable() {
        const notes = document.querySelectorAll('.note');
        notes.forEach(note => {
            note.classList.toggle('selectable', isSelectMode);
            if (!isSelectMode) {
                note.classList.remove('selected');
            }
        });
    }

    function updateButtonsVisibility() {
        const selectedCount = document.querySelectorAll('.note.selected').length;
        selectNotesButton.textContent = isSelectMode ? 'Отменить выбор' : 'Выбрать';
        restoreSelectedButton.style.display = selectedCount > 0 ? 'inline-block' : 'none';
        deleteSelectedButton.style.display = selectedCount > 0 ? 'inline-block' : 'none';
        
        if (isSelectMode) {
            restoreSelectedButton.textContent = `Восстановить (${selectedCount})`;
            deleteSelectedButton.textContent = `Удалить (${selectedCount})`;
        }
    }

    if (notesContainer) {
        notesContainer.addEventListener('click', handleNoteClick);
    }

    function handleNoteClick(event) {
        if (!isSelectMode) return;
        const note = event.target.closest('.note');
        if (note) {
            event.preventDefault();
            event.stopPropagation();
            note.classList.toggle('selected');
            updateButtonsVisibility();
        }
    }

    if (restoreSelectedButton) {
        restoreSelectedButton.addEventListener('click', restoreSelectedNotes);
    }

    if (deleteSelectedButton) {
        deleteSelectedButton.addEventListener('click', deleteSelectedNotes);
    }

    if (deleteAllButton) {
        deleteAllButton.addEventListener('click', deleteAllNotes);
    }

    function restoreSelectedNotes() {
        const selectedNotes = document.querySelectorAll('.note.selected');
        const noteIds = Array.from(selectedNotes).map(note => note.dataset.id);
        
        fetch('/restore_notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ note_ids: noteIds }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                selectedNotes.forEach(note => note.remove());
                toggleSelectMode();
            } else {
                alert('Ошибка при восстановлении заметок');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при восстановлении заметок');
        });
    }

    function deleteSelectedNotes() {
        if (confirm('Вы уверены, что хотите удалить выбранные заметки?')) {
            const selectedNotes = document.querySelectorAll('.note.selected');
            const noteIds = Array.from(selectedNotes).map(note => note.dataset.id);
            
            fetch('/delete_notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ note_ids: noteIds }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedNotes.forEach(note => note.remove());
                    toggleSelectMode();
                } else {
                    alert('Ошибка при удалении заметок');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при удалении заметок');
            });
        }
    }

    function deleteAllNotes() {
        if (confirm('Вы уверены, что хотите удалить все архивированные заметки?')) {
            fetch('/delete_all_archived', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const notes = document.querySelectorAll('.note');
                    notes.forEach(note => note.remove());
                    toggleSelectMode();
                } else {
                    alert('Ошибка при удалении всех заметок');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при удалении всех заметок');
            });
        }
    }
});