let currentNoteId = null;
let saveTimeout;
let attachmentsContainer;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен');
    console.log('add-image button:', document.getElementById('add-image'));
    console.log('add-file button:', document.getElementById('add-file'));

    const noteForm = document.getElementById('note-form');
    currentNoteId = noteForm ? noteForm.dataset.noteId : null;
    console.log('currentNoteId:', currentNoteId);

    if (!currentNoteId) {
        console.error('ID заметки не определен в форме');
        // Создаем новую заметку
        fetch('/note', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: '',
                content: '',
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentNoteId = data.id;
                noteForm.dataset.noteId = currentNoteId;
                console.log('Новая заметка создана с ID:', currentNoteId);
            } else {
                throw new Error(data.error || 'Ошибка при создании заметки');
            }
        })
        .catch(error => {
            console.error('Ошибка при создании заметки:', error);
            alert('Ошибка при создании заметки: ' + error.message);
        });
    }

    const noteTitle = document.getElementById('note-title');
    const noteContent = document.getElementById('note-content');
    const addImageButton = document.getElementById('add-image');
    const addFileButton = document.getElementById('add-file');
    attachmentsContainer = document.getElementById('attachments');

    if (noteForm) {
        const initialColor = noteForm.style.backgroundColor || '#202124';
        const initialTextColor = noteForm.style.color || '#e8eaed';
        
        noteForm.style.backgroundColor = initialColor;
        noteForm.style.color = initialTextColor;
        if (noteTitle) noteTitle.style.color = initialTextColor;
        if (noteContent) noteContent.style.color = initialTextColor;
    }

    if (addImageButton) {
        addImageButton.addEventListener('click', function() {
            handleFileUpload('image', '/upload_image');
        });
    }

    if (addFileButton) {
        addFileButton.addEventListener('click', function() {
            handleFileUpload('file', '/upload_file');
        });
    }

    function autoResizeTextarea() {
        noteContent.style.height = 'auto';
        noteContent.style.height = noteContent.scrollHeight + 'px';
    }

    async function createEmptyNote() {
        try {
            const response = await fetch('/note', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: '', content: '', color: '' }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            currentNoteId = data.id;
            noteForm.dataset.noteId = currentNoteId;
            console.log('Новая заметка создана с ID:', currentNoteId);
        } catch (error) {
            console.error('Ошибка при создании новой заметки:', error);
        }
    }

    function initializeAttachments() {
        const attachments = document.querySelectorAll('.attachment');
        attachments.forEach(attachment => {
            const removeButton = attachment.querySelector('.remove-attachment');
            if (removeButton) {
                removeButton.addEventListener('click', function() {
                    const attachmentUrl = attachment.querySelector('a').href;
                    if (confirm('Вы уверены, что хотите удалить это вложение?')) {
                        deleteAttachment(attachmentUrl, attachment);
                    }
                });
            }
        });
    }

    function debounce(func, wait) {
        return function(...args) {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    const debouncedSaveNote = debounce(saveNote, 1000);

    noteTitle.addEventListener('input', debouncedSaveNote);
    noteContent.addEventListener('input', () => {
        autoResizeTextarea();
        debouncedSaveNote();
    });

    // Остальной код без упоминаний colorPalette

    // Добавляем обработчик для открытия изображения в новой вкладке
    document.addEventListener('click', function(e) {
        if (e.target.closest('.open-image')) {
            e.preventDefault();
            const imageUrl = e.target.closest('.open-image').getAttribute('href');
            window.open(imageUrl, '_blank');
        }
    });

    function handleFileUpload(type, url) {
        console.log('handleFileUpload вызвана', type, url);
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = type === 'image' ? 'image/*' : '*/*';
        fileInput.style.display = 'none';
        
        fileInput.addEventListener('change', function() {
            const file = fileInput.files[0];
            if (!file) {
                console.log('Файл не выбран');
                return;
            }

            console.log('Выбран файл:', file.name);
            const formData = new FormData();
            formData.append('file', file);
            formData.append('note_id', document.getElementById('note-form').dataset.noteId);

            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Ответ сервера:', data);
                if (data.success) {
                    updateAttachmentUI(data, type);
                } else {
                    alert('Ошибк при загрузке файла: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при загрузке айла');
            });
        });

        document.body.appendChild(fileInput);
        fileInput.click();
        document.body.removeChild(fileInput);
    }

    function deleteAttachment(attachmentUrl, attachmentElement) {
        console.log('Начало удаления вложения', attachmentUrl);
        // Извлекаем ID заметки и имя файла из полного URL
        const urlParts = attachmentUrl.split('/');
        const noteId = urlParts[urlParts.length - 2];
        const fileName = urlParts[urlParts.length - 1];
        let deleteUrl = `/delete_attachment/${noteId}/${encodeURIComponent(fileName)}`;
        console.log('URL для удаления:', deleteUrl);
        fetch(deleteUrl, {
            method: 'DELETE',
        })
        .then(response => {
            console.log('Получен ответ от сервера', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные ответа:', data);
            if (data.success) {
                console.log('Удаление успешно, удаляем элемент из DOM');
                attachmentElement.remove();
                console.log('Элемент удален из DOM');
                if (attachmentsContainer && attachmentsContainer.children.length === 0) {
                    attachmentsContainer.remove();
                }
                saveNote();
            } else {
                console.error('Ошибка при удалении:', data.error);
                alert('Ошибка при удалении вложения: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении:', error);
            alert('Произошла ошибка при удалении вложения');
        });
    }

    function saveNote() {
        if (!currentNoteId) {
            console.error('ID заметки не определен');
            // Создаем новую заметку
            fetch('/note', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: noteTitle.value,
                    content: noteContent.value,
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentNoteId = data.id;
                    console.log('Новая заметка создана с ID:', currentNoteId);
                    updateNoteContent();
                } else {
                    throw new Error(data.error || 'Ошибка при создании заметки');
                }
            })
            .catch(error => {
                console.error('Ошибка при создании заметки:', error);
                alert('Ошибка при создании аметки: ' + error.message);
            });
            return;
        }

        const noteData = {
            title: noteTitle.value,
            content: noteContent.value,
            attachments: []
        };

        if (attachmentsContainer) {
            noteData.attachments = Array.from(attachmentsContainer.querySelectorAll('.attachment, .attachment-image')).map(attachment => {
                const removeButton = attachment.querySelector('.remove-attachment, .attachment-delete');
                const linkOrImg = attachment.querySelector('a, img');
                return {
                    type: removeButton ? removeButton.dataset.type : 'image',
                    url: linkOrImg ? (linkOrImg.href || linkOrImg.src) : ''
                };
            });
        }

        console.log('Отправляемые данные:', noteData);

        fetch(`/note/${currentNoteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(noteData),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Полученные данные:', data);
            if (data.success) {
                console.log('Заметка сохранена');
                updateLastModified(data.updated_at, data.formatted_time);
            } else {
                throw new Error(data.error || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error('Ошибка при сохранении заметки:', error.message);
            alert('Ошибка при сохранении заметки: ' + error.message);
        });
    }

    function updateLastModified(updatedAt, formattedTime) {
        const noteDate = document.querySelector('.note-date time');
        if (noteDate) {
            noteDate.textContent = formattedTime;
            noteDate.setAttribute('datetime', updatedAt);
        }
    }

    function updateAttachmentUI(data, type) {
        if (!attachmentsContainer) {
            attachmentsContainer = document.createElement('div');
            attachmentsContainer.id = 'attachments';
            document.getElementById('note-form').insertBefore(attachmentsContainer, document.getElementById('note-title'));
        }

        const newAttachment = document.createElement('div');
        newAttachment.className = 'attachment';
        newAttachment.innerHTML = `
            <a href="${data.file_url}" target="_blank">${data.filename}</a>
            <button type="button" class="remove-attachment" data-type="${type}">Удалить</button>
        `;
        newAttachment.dataset.id = data.file_url.split('/').pop();
        attachmentsContainer.appendChild(newAttachment);

        // Добавляем обработчик события для кнопки удаления
        const deleteButton = newAttachment.querySelector('.remove-attachment');
        if (deleteButton) {
            deleteButton.addEventListener('click', function() {
                if (confirm('Вы уверены, что хотите удалить это вложение?')) {
                    deleteAttachment(data.file_url, newAttachment);
                }
            });
        }

        saveNote();
    }

    // ... остальной код ...
    initializeAttachments();
});

console.log('note.js загружен');
