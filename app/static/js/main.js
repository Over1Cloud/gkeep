function handleFileUpload(type, url) {
    console.log('handleFileUpload вызвана', new Date().toISOString());
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = type === 'image' ? 'image/*' : '*/*';
    fileInput.style.display = 'none';
    
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (!file) return;

        if (file.size > 200 * 1024 * 1024) {
            alert('Файл слишком большой. Максимальный размер - 200 МБ.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        const noteId = document.getElementById('note-form').dataset.noteId;
        if (noteId) {
            formData.append('note_id', noteId);
        } else {
            console.warn('note_id е найден, создаем новую заметку');
            createEmptyNote().then(newNoteId => {
                formData.append('note_id', newNoteId);
                uploadFile(formData, type, url);
            });
            return;
        }

        uploadFile(formData, type, url);
    });

    document.body.appendChild(fileInput);
    fileInput.click();
}

function uploadFile(formData, type, url) {
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(text || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Ответ сервера:', data);
        updateAttachmentUI(data, type);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при загрузке файла: ' + error.message);
    })
    .finally(() => {
        // Удаляем элемент ввода файла после использования
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.remove();
        }
    });
}

function updateAttachmentUI(data, type) {
    console.log('Обновление UI для вложения:', data, type);
    const attachmentsContainer = document.getElementById('attachments');
    if (!attachmentsContainer) return;

    const attachment = document.createElement('div');
    attachment.className = 'attachment';
    attachment.dataset.tempPath = data.temp_image_path;

    if (type === 'image') {
        attachment.innerHTML = `
            <img src="${data.file_url}" alt="Прикрепленное изображение" style="max-width: 200px;">
            <button type="button" class="remove-attachment" data-type="image">Удалить</button>
        `;
    } else {
        attachment.innerHTML = `
            <a href="${data.file_url}" target="_blank">Прикрепленный файл</a>
            <button type="button" class="remove-attachment" data-type="file">Удалить</button>
        `;
    }

    attachmentsContainer.appendChild(attachment);
    console.log('Вложение добавлено в DOM');

    // Добавляем обработчик для кнопки удаления
    const removeButton = attachment.querySelector('.remove-attachment');
    removeButton.addEventListener('click', function() {
        attachment.remove();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация функций для работы с заметками
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
            const note = event.target.closest('.note');
            if (!note) return;

            if (isSelectMode) {
                event.preventDefault();
                event.stopPropagation();
                note.classList.toggle('selected');
                updateSelectedCount();
            } else {
                // Переход к редактированию заметки
                const noteId = note.dataset.id;
                window.location.href = `/note/${noteId}`;
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

    // Инициализация других функций, если необходимо

    const addNoteButton = document.getElementById('add-note');
    
    if (addNoteButton) {
        addNoteButton.addEventListener('click', function() {
            window.location.href = '/note';  // Предполагается, что у вас есть маршрут '/note' для создания новой заметки
        });
    }
});
