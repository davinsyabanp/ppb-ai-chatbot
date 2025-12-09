/**
 * Admin Dashboard JavaScript
 * Handles all dashboard functionality including file management, modal operations,
 * toast notifications, and knowledge base operations
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - 'success' or 'danger'
     */
    function showToast(message, type = 'success') {
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        const bgColor = type === 'success' 
            ? 'bg-gradient-to-r from-green-500 to-green-600' 
            : 'bg-gradient-to-r from-red-500 to-red-600';
        
        toast.className = `flex items-center px-6 py-4 rounded-xl shadow-2xl mb-4 text-white ${bgColor} backdrop-blur-sm border border-white/20 transform translate-x-full transition-all duration-300`;
        toast.id = toastId;
        toast.innerHTML = `
            <i class="bi ${type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} mr-3 text-lg"></i>
            <span class='flex-1 font-medium'>${message}</span>
            <button class='ml-4 text-white hover:text-gray-200 transition-colors text-xl' onclick='this.parentElement.remove()'>&times;</button>
        `;
        document.getElementById('toast-container').appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 3.5 seconds
        setTimeout(() => {
            if (toast) {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }
        }, 3500);
    }

    /**
     * Open modal by ID
     * @param {string} id - Modal element ID
     */
    function openModal(id) {
        document.getElementById(id).classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Close modal by ID
     * @param {string} id - Modal element ID
     */
    function closeModal(id) {
        document.getElementById(id).classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    // Modal event listeners for delete buttons
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.getElementById('modal-file-name').textContent = this.getAttribute('data-file-name');
            const fileId = this.getAttribute('data-file-id');
            const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
            confirmDeleteBtn.onclick = function() {
                deleteFile(fileId);
            };
            openModal('deleteModal');
        });
    });

    // Modal close buttons
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', function() {
            closeModal(this.getAttribute('data-modal-close'));
        });
    });

    // Close modal on backdrop click
    document.getElementById('deleteModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal('deleteModal');
        }
    });

    /**
     * Refresh knowledge base table with latest files
     */
    function refreshKnowledgeBaseTable() {
        fetch('/api/files')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector('table tbody');
                if (tableBody && data.files) {
                    tableBody.innerHTML = '';
                    data.files.forEach(file => {
                        const row = document.createElement('tr');
                        row.className = 'border-t border-slate-200 hover:bg-slate-50 transition-colors';
                        row.innerHTML = `
                            <td class="px-6 py-4 text-slate-800 font-medium">${file.filename}</td>
                            <td class="px-6 py-4 text-slate-600">${file.filetype}</td>
                            <td class="px-6 py-4 text-slate-600">${file.uploaded_at}</td>
                            <td class="px-6 py-4">
                                <button class="text-red-600 hover:bg-red-50 rounded-lg p-2 transition-all duration-200 hover:scale-110 delete-btn" data-bs-toggle="modal" data-bs-target="#deleteModal" data-file-id="${file.id}" data-file-name="${file.filename}" title="Delete this file">
                                    <i class="bi bi-trash text-lg"></i>
                                </button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                }
            })
            .catch(error => {
                console.error('Error refreshing knowledge base table:', error);
            });
    }

    /**
     * Delete a file from knowledge base
     * @param {number} fileId - File ID to delete
     */
    function deleteFile(fileId) {
        fetch(`/api/admin/delete/${fileId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                showToast('File deleted successfully!', 'success');
                closeModal('deleteModal');
                refreshKnowledgeBaseTable();
                // Immediately check KB status after delete
                setTimeout(() => pollKBStatus(), 500);
            } else {
                throw new Error('Delete failed');
            }
        })
        .catch(error => {
            showToast('Delete failed. Please try again.', 'danger');
            console.error('Error deleting file:', error);
        });
    }

    /**
     * Poll knowledge base status
     */
    function pollKBStatus() {
        fetch('/api/kb_status')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const statusMsg = document.getElementById('kb-status-message');
                const embedBtn = document.getElementById('embed-data-btn');
                
                if (!statusMsg || !embedBtn) {
                    console.warn('Status elements not found');
                    return;
                }
                
                if (data.status === 'requires_embedding') {
                    // Files exist but not all embedded, or new files added - BUTTON ENABLED
                    statusMsg.innerHTML = '<span class="inline-flex items-center px-3 py-2 rounded-full bg-yellow-100 text-yellow-800 text-sm font-semibold status-message"><i class="bi bi-exclamation-triangle mr-2"></i>New or unembed files detected. Click "Embed Data" to update.</span>';
                    embedBtn.disabled = false;
                    embedBtn.className = 'w-full py-4 px-6 rounded-xl font-semibold transition-all duration-200 text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-sm shadow-lg hover:shadow-xl transform hover:scale-[1.02]';
                    console.log('✅ Embed button ENABLED - files need embedding');
                } else if (data.status === 'active') {
                    // All files embedded and up to date - BUTTON DISABLED
                    statusMsg.innerHTML = '<span class="inline-flex items-center px-3 py-2 rounded-full bg-green-100 text-green-800 text-sm font-semibold status-message"><i class="bi bi-check-circle mr-2"></i>All files are embedded and up to date.</span>';
                    embedBtn.disabled = true;
                    embedBtn.className = 'w-full py-4 px-6 rounded-xl font-semibold transition-all duration-200 text-white bg-slate-400 cursor-not-allowed text-sm shadow-lg';
                    console.log('✅ Embed button DISABLED - all files up to date');
                } else if (data.status === 'no_files') {
                    // No files uploaded - BUTTON DISABLED
                    statusMsg.innerHTML = '<span class="inline-flex items-center px-3 py-2 rounded-full bg-slate-100 text-slate-700 text-sm font-semibold status-message"><i class="bi bi-info-circle mr-2"></i>No files uploaded yet. Upload files first.</span>';
                    embedBtn.disabled = true;
                    embedBtn.className = 'w-full py-4 px-6 rounded-xl font-semibold transition-all duration-200 text-white bg-slate-400 cursor-not-allowed text-sm shadow-lg';
                    console.log('✅ Embed button DISABLED - no files');
                } else {
                    console.warn(`Unknown status: ${data.status}`);
                }
            })
            .catch(error => {
                console.error('Error polling KB status:', error);
            });
    }

    /**
     * Poll embedding progress
     */
    function pollEmbedProgress() {
        fetch('/api/admin/embed_progress')
            .then(response => response.json())
            .then(data => {
                const progressBar = document.getElementById('embed-progress-bar');
                const progressInner = document.getElementById('embed-progress-inner');
                const progressText = document.getElementById('embed-progress-text');
                const embedBtn = document.getElementById('embed-data-btn');
                if (data.status === 'running' || data.status === 'starting') {
                    progressBar.classList.remove('hidden');
                    progressInner.style.width = (data.progress || 0) + '%';
                    progressText.textContent = data.message || 'Embedding in progress...';
                    embedBtn.disabled = true;
                    embedBtn.className = 'w-full py-4 px-6 rounded-xl font-semibold transition-all duration-200 text-white bg-slate-400 cursor-not-allowed text-sm shadow-lg';
                } else {
                    progressBar.classList.add('hidden');
                    progressInner.style.width = '0%';
                    progressText.textContent = '';
                }
            });
    }

    // Initialize polling
    pollKBStatus();
    pollEmbedProgress();
    setInterval(pollKBStatus, 3000);
    setInterval(pollEmbedProgress, 1500);
    
    document.getElementById('embed-form').addEventListener('submit', function() {
        setTimeout(() => pollEmbedProgress(), 500);
    });

    // Chunking Preview Logic
    const previewBtn = document.getElementById('preview-btn');
    const processBtn = document.getElementById('process-btn');
    const previewArea = document.getElementById('preview-area');
    const previewChunks = document.getElementById('preview-chunks');
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    let previewed = false;

    previewBtn.addEventListener('click', function() {
        const chunkSize = document.getElementById('chunk-size').value;
        const chunkOverlap = document.getElementById('chunk-overlap').value;
        if (!fileInput.files.length) {
            showToast('Please select a file first.', 'danger');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('chunk_size', chunkSize);
        formData.append('chunk_overlap', chunkOverlap);
        previewBtn.disabled = true;
        previewBtn.innerHTML = '<i class="bi bi-hourglass-split me-3 animate-spin"></i>Loading...';
        
        fetch('/api/preview-chunking', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            previewBtn.disabled = false;
            previewBtn.innerHTML = '<i class="bi bi-eye me-3"></i>Preview Chunking';
            if (data.success) {
                if (data.preview_chunks && data.preview_chunks.length > 0) {
                    previewArea.classList.remove('hidden');
                    previewChunks.innerHTML = '';
                    data.preview_chunks.forEach(chunk => {
                        const div = document.createElement('div');
                        div.className = 'mb-4 p-4 bg-white border-2 border-slate-200 rounded-xl shadow-sm';
                        div.innerHTML = `<div class="font-semibold text-slate-800 mb-3 text-sm">Chunk ${chunk.chunk_number}:</div><pre class='whitespace-pre-wrap text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200'>${chunk.content}</pre>`;
                        previewChunks.appendChild(div);
                    });
                    processBtn.disabled = false;
                    previewed = true;
                } else {
                    previewArea.classList.remove('hidden');
                    previewChunks.innerHTML = `<div class='text-yellow-700 bg-yellow-50 p-4 rounded-xl text-sm border-2 border-yellow-200'><i class="bi bi-exclamation-triangle mr-2"></i>No preview chunks could be generated. The file may not contain extractable text or may be scanned images.</div>`;
                    processBtn.disabled = true;
                    previewed = false;
                }
            } else {
                previewArea.classList.remove('hidden');
                previewChunks.innerHTML = `<div class='text-red-700 bg-red-50 p-4 rounded-xl text-sm border-2 border-red-200'><i class="bi bi-x-circle mr-2"></i>${data.error || 'Preview failed.'}</div>`;
                processBtn.disabled = true;
                previewed = false;
            }
        })
        .catch(err => {
            previewBtn.disabled = false;
            previewBtn.innerHTML = '<i class="bi bi-eye me-3"></i>Preview Chunking';
            previewArea.classList.remove('hidden');
            previewChunks.innerHTML = `<div class='text-red-700 bg-red-50 p-4 rounded-xl text-sm border-2 border-red-200'><i class="bi bi-x-circle mr-2"></i>Preview failed. Please try again.</div>`;
            processBtn.disabled = true;
            previewed = false;
        });
    });

    // Form submission for file upload
    uploadForm.addEventListener('submit', function(e) {
        if (!previewed) {
            e.preventDefault();
            showToast('Please preview chunking before processing.', 'danger');
            return;
        }
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        processBtn.disabled = true;
        processBtn.innerHTML = '<i class="bi bi-hourglass-split me-3 animate-spin"></i>Uploading...';
        
        fetch('/admin', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (!res.ok) {
                throw new Error('Upload failed');
            }
            return res.text();
        })
        .then(html => {
            showToast('File uploaded successfully!', 'success');
            fileInput.value = '';
            previewed = false;
            previewArea.classList.add('hidden');
            previewChunks.innerHTML = '';
            processBtn.disabled = true;
            processBtn.innerHTML = '<i class="bi bi-check-circle me-3"></i>Process and Save to Knowledge Base';
            refreshKnowledgeBaseTable();
        })
        .catch(err => {
            showToast('Upload failed. Please try again.', 'danger');
            processBtn.disabled = false;
            processBtn.innerHTML = '<i class="bi bi-check-circle me-3"></i>Process and Save to Knowledge Base';
        });
    });

    // Event delegation for dynamically added delete buttons
    const tableBody = document.querySelector('table tbody');
    if (tableBody) {
        tableBody.addEventListener('click', function(event) {
            const btn = event.target.closest('[data-bs-toggle="modal"]');
            if (btn) {
                document.getElementById('modal-file-name').textContent = btn.getAttribute('data-file-name');
                const fileId = btn.getAttribute('data-file-id');
                const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
                confirmDeleteBtn.onclick = function() {
                    deleteFile(fileId);
                };
                openModal('deleteModal');
            }
        });
    }

    // Make showToast globally accessible for Jinja2 templates
    window.showToast = showToast;
});
