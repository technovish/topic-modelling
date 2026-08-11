document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const browseBtn = document.getElementById('browseBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const statusMessage = document.getElementById('statusMessage');

    let selectedFile = null;

    // Trigger file input when clicking browse button or drop zone
    dropZone.addEventListener('click', () => fileInput.click());

    // Prevent default behavior for drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('drag-active');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drag-active');
    }

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    // Handle selected files from input
    fileInput.addEventListener('change', function () {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        // Clear previous list
        fileList.innerHTML = '';
        selectedFile = null;
        analyzeBtn.disabled = true;
        statusMessage.textContent = '';
        statusMessage.className = 'status-message';

        const validFiles = [...files].filter(file => file.name.match(/\.(csv|xlsx|xls)$/i));

        if (validFiles.length > 0) {
            // Only process the first file for now
            selectedFile = validFiles[0];
            addFileToList(selectedFile);
            analyzeBtn.disabled = false;
        } else if (files.length > 0) {
            alert('Please select a valid CSV or Excel file.');
        }
    }

    function addFileToList(file) {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
      <div class="file-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
      </div>
      <span class="file-name">${file.name}</span>
      <button class="remove-btn" title="Remove file" onclick="event.stopPropagation(); removeFile()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    `;
        fileList.appendChild(div);
    }

    window.removeFile = function () {
        fileList.innerHTML = '';
        selectedFile = null;
        analyzeBtn.disabled = true;
        fileInput.value = ''; // Reset input
    }

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Uploading...';
        statusMessage.textContent = '';

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                statusMessage.textContent = `Success: ${result.message} (${result.rows} rows). Redirecting...`;
                statusMessage.classList.add('status-success');
                setTimeout(() => {
                    window.location.href = '/results';
                }, 1000); // Short delay to show success message
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            statusMessage.textContent = `Error: ${error.message}`;
            statusMessage.classList.add('status-error');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Data';
        }
    });
});
