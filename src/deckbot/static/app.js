document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatHistory = document.getElementById('chat-history');
    const messageInput = document.getElementById('message-input');
    const btnSend = document.getElementById('btn-send');
    const imageGallery = document.getElementById('image-gallery');
    const thinkingIndicator = document.getElementById('thinking-indicator');
    const presentationSelect = document.getElementById('presentation-select');
    const presentationList = document.getElementById('presentation-list');
    const presentationCreate = document.getElementById('presentation-create');
    const btnCancelCreate = document.getElementById('btn-cancel-create');
    // const currentPresentation = document.getElementById('current-presentation'); // Removed from UI
    
    // Menu items
    const menuNew = document.getElementById('menu-new');
    const menuOpen = document.getElementById('menu-open');
    const menuExport = document.getElementById('menu-export');
    
    // Sidebar elements
    const viewPreview = document.getElementById('view-preview');
    const viewImages = document.getElementById('view-images');
    const previewFrame = document.getElementById('preview-frame');
    const btnCloseImages = document.getElementById('btn-close-images');
    
    // Preferences elements
    const preferencesModal = document.getElementById('preferences-modal');
    const prefTheme = document.getElementById('pref-theme');
    const btnSavePreferences = document.getElementById('btn-save-preferences');
    const btnCancelPreferences = document.getElementById('btn-cancel-preferences');
    const menuPreferences = document.getElementById('menu-preferences');
    const menuAbout = document.getElementById('menu-about');
    
    // Theme buttons
    const themeBtns = document.querySelectorAll('.theme-btn');
    
    // Color theme options
    const colorThemeOptions = document.querySelectorAll('.color-theme-option');
    
    let currentPresName = "";
    let currentColorTheme = "miami"; // Default

    // ===== Theme Management =====
    function setTheme(theme, saveToBackend = true) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update button states
        themeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
        
        // Update preferences dropdown if it exists
        if (prefTheme) {
            prefTheme.value = theme;
        }
        
        // Save to backend
        if (saveToBackend) {
            fetch('/api/preferences/theme', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({value: theme})
            }).catch(err => console.error('Error saving theme preference:', err));
        }
    }
    
    // ===== Color Theme Management =====
    function setColorTheme(colorTheme, saveToBackend = true) {
        currentColorTheme = colorTheme;
        document.documentElement.setAttribute('data-color-theme', colorTheme);
        
        // Update active state
        colorThemeOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.theme === colorTheme);
        });
        
        // Save to backend
        if (saveToBackend) {
            fetch('/api/preferences/color_theme', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({value: colorTheme})
            }).catch(err => console.error('Error saving color theme preference:', err));
        }
    }
    
    // Load saved theme from backend
    function loadThemePreference() {
        fetch('/api/preferences/theme')
            .then(r => r.json())
            .then(data => {
                if (data.value) {
                    setTheme(data.value, false);
                } else {
                    // Default to system theme if no preference saved
                    setTheme('system', false);
                }
            })
            .catch(() => {
                // Fallback to system if backend fails
                setTheme('system', false);
            });
    }
    
    function loadColorThemePreference() {
        fetch('/api/preferences/color_theme')
            .then(r => r.json())
            .then(data => {
                if (data.value) {
                    setColorTheme(data.value, false);
                } else {
                    // Default to Miami theme if no preference saved
                    setColorTheme('miami', false);
                }
            })
            .catch(() => {
                // Fallback to Miami if backend fails
                setColorTheme('miami', false);
            });
    }
    
    loadThemePreference();
    loadColorThemePreference();
    
    // Theme button handlers
    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            setTheme(btn.dataset.theme);
        });
    });
    
    // Preferences theme selector
    if (prefTheme) {
        prefTheme.addEventListener('change', () => {
            setTheme(prefTheme.value, false); // Don't save yet, wait for Save button
        });
    }
    
    // Color theme option handlers
    colorThemeOptions.forEach(option => {
        option.addEventListener('click', () => {
            setColorTheme(option.dataset.theme, false); // Don't save yet, wait for Save button
        });
    });
    
    // Open preferences dialog
    function openPreferences() {
        // Load current preferences
        fetch('/api/preferences')
            .then(r => r.json())
            .then(prefs => {
                if (prefs.theme && prefTheme) {
                    prefTheme.value = prefs.theme;
                }
                if (preferencesModal) {
                    preferencesModal.classList.remove('hidden');
                    refreshIcons();
                }
            })
            .catch(err => {
                console.error('Error loading preferences:', err);
                // Show dialog anyway
                if (preferencesModal) {
                    preferencesModal.classList.remove('hidden');
                    refreshIcons();
                }
            });
    }
    
    // Helper to refresh Lucide icons
    function refreshIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // ===== Resizable Sidebar (Improved) =====
    const resizer = document.querySelector('.resizer');
    const sidebar = document.querySelector('.sidebar');
    const container = document.querySelector('.container');
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    resizer.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isResizing = true;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        
        // Add visual feedback
        resizer.classList.add('resizing');
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
        
        // Prevent text selection and iframe interaction during resize
        const iframe = document.getElementById('preview-frame');
        if (iframe) {
            iframe.style.pointerEvents = 'none';
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        e.preventDefault();
        
        // Calculate new width based on mouse movement
        const dx = startX - e.clientX;
        const newWidth = startWidth + dx;
        
        // Apply constraints
        const minWidth = 300;
        const maxWidth = 1200;
        const containerWidth = container.offsetWidth;
        const maxAllowed = Math.min(maxWidth, containerWidth - 400); // Ensure chat has at least 400px
        
        if (newWidth >= minWidth && newWidth <= maxAllowed) {
            sidebar.style.width = newWidth + 'px';
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Re-enable iframe interaction
            const iframe = document.getElementById('preview-frame');
            if (iframe) {
                iframe.style.pointerEvents = '';
            }
        }
    });
    
    // Handle mouse leaving window during resize
    document.addEventListener('mouseleave', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            const iframe = document.getElementById('preview-frame');
            if (iframe) {
                iframe.style.pointerEvents = '';
            }
        }
    });

    // ===== Menu Handlers =====
    menuNew.addEventListener('click', () => {
        presentationSelect.classList.add('hidden');
        presentationCreate.classList.remove('hidden');
        loadTemplates();
    });
    
    // Create New button (using event delegation since it's in the HTML)
    document.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'btn-create-new') {
            presentationSelect.classList.add('hidden');
            presentationCreate.classList.remove('hidden');
            loadTemplates();
        }
    });
    
    menuOpen.addEventListener('click', () => {
        presentationSelect.classList.remove('hidden');
        presentationCreate.classList.add('hidden');
        loadPresentationList();
    });
    
    if (menuAbout) {
        menuAbout.addEventListener('click', () => {
            alert('DeckBot v1.0\n\nAn AI-powered presentation creation tool.\n\nBuilt with Marp, Google Gemini, and Nano Banana.');
        });
    }
    
    if (menuPreferences) {
        menuPreferences.addEventListener('click', () => {
            openPreferences();
        });
    }
    
    if (btnSavePreferences) {
        btnSavePreferences.addEventListener('click', () => {
            // Save both theme and color theme
            const promises = [];
            
            if (prefTheme) {
                promises.push(
                    fetch('/api/preferences/theme', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({value: prefTheme.value})
                    })
                );
            }
            
            promises.push(
                fetch('/api/preferences/color_theme', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({value: currentColorTheme})
                })
            );
            
            Promise.all(promises)
                .then(() => {
                    preferencesModal.classList.add('hidden');
                })
                .catch(err => {
                    console.error('Error saving preferences:', err);
                    preferencesModal.classList.add('hidden');
                });
        });
    }
    
    if (btnCancelPreferences) {
        btnCancelPreferences.addEventListener('click', () => {
            // Reload preferences to undo any unsaved changes
            loadThemePreference();
            loadColorThemePreference();
            preferencesModal.classList.add('hidden');
        });
    }
    
    menuExport.addEventListener('click', () => {
        // TODO: Implement export
        alert('Export functionality coming soon!');
    });
    
    // Mac-style keyboard shortcut: Cmd+,
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === ',') {
            e.preventDefault();
            openPreferences();
        }
    });
    
    if (btnCancelCreate) {
        btnCancelCreate.addEventListener('click', () => {
            presentationCreate.classList.add('hidden');
            presentationSelect.classList.remove('hidden');
        });
    }

    // ===== View Switching =====
    function switchView(viewName) {
        if (viewName === 'preview') {
            viewPreview.style.display = 'block';
            viewImages.style.display = 'none';
        } else if (viewName === 'images') {
            viewImages.style.display = 'flex';
            viewPreview.style.display = 'none';
        }
    }
    
    btnCloseImages.addEventListener('click', () => {
        switchView('preview');
    });

    // Default view - always start with preview
    switchView('preview');

    function reloadPreview() {
        previewFrame.src = `/api/presentation/preview?t=${new Date().getTime()}`;
    }

    // ===== Template Loading =====
    function loadTemplates() {
        fetch('/api/templates')
            .then(r => r.json())
            .then(templates => {
                const select = document.getElementById('new-pres-template');
                select.innerHTML = '<option value="">No template</option>';
                templates.forEach(t => {
                    const option = document.createElement('option');
                    option.value = t.name;
                    option.textContent = t.name;
                    select.appendChild(option);
                });
            });
    }

    // ===== Presentation List =====
    function loadPresentationList() {
        fetch('/api/presentations')
            .then(r => r.json())
            .then(presos => {
                presentationList.innerHTML = '';
                
                if (presos.length === 0) {
                    // Show empty state
                    const emptyMsg = document.createElement('p');
                    emptyMsg.className = 'placeholder';
                    emptyMsg.textContent = 'No presentations yet. Click "Create New" below to get started.';
                    presentationList.appendChild(emptyMsg);
                } else {
                    presos.forEach(p => {
                        const li = document.createElement('li');
                        
                        const nameSpan = document.createElement('span');
                        nameSpan.className = 'pres-name';
                        nameSpan.textContent = `${p.name} - ${p.description || ''}`;
                        nameSpan.onclick = () => loadPresentation(p.name);
                        
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'btn-delete';
                        deleteBtn.textContent = 'Delete';
                        deleteBtn.onclick = (e) => {
                            e.stopPropagation();
                            deletePresentation(p.name);
                        };
                        
                        li.appendChild(nameSpan);
                        li.appendChild(deleteBtn);
                        presentationList.appendChild(li);
                    });
                }
                
                refreshIcons();
            })
            .catch(err => {
                console.error('Error loading presentations:', err);
                if (presentationList) {
                    presentationList.innerHTML = '<p class="placeholder">Error loading presentations. Check console for details.</p>';
                }
            });
    }

    function deletePresentation(name) {
        if (!confirm(`Are you sure you want to delete "${name}"?\n\nThis cannot be undone.`)) {
            return;
        }

        fetch('/api/presentations/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                loadPresentationList();
            }
        })
        .catch(err => {
            alert('Error deleting presentation: ' + err);
        });
    }

    function loadPresentation(name) {
        fetch('/api/load', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        })
        .then(r => r.json())
        .then(data => {
            currentPresName = name;
            // currentPresentation.textContent = name; // Element removed from UI
            presentationSelect.classList.add('hidden');
            
            // Always show preview when loading a presentation
            switchView('preview');
            
            // Load preview
            reloadPreview();
            
            // Load chat history
            chatHistory.innerHTML = '';
            if (data.history) {
                data.history.forEach(msg => {
                    if (msg.role !== 'system') {
                        appendMessage(msg.role, msg.parts[0].text || msg.parts[0]);
                    }
                });
            }
        });
    }

    // ===== Create Presentation =====
    document.getElementById('create-form').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const name = document.getElementById('new-pres-name').value;
        const description = document.getElementById('new-pres-desc').value;
        const template = document.getElementById('new-pres-template').value;
        
        fetch('/api/presentations/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, description, template})
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                presentationCreate.classList.add('hidden');
                loadPresentation(name);
            }
        });
    });

    // ===== Chat Functions =====
    function appendMessage(role, content) {
        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        // Set avatar content
        if (role === 'user') {
            avatar.innerHTML = '<i data-lucide="user" style="width: 16px; height: 16px;"></i>';
        } else if (role === 'model') {
            avatar.innerHTML = '<i data-lucide="bot" style="width: 16px; height: 16px;"></i>';
        } else if (role === 'system') {
            avatar.innerHTML = '<i data-lucide="terminal" style="width: 16px; height: 16px;"></i>';
        }
        
        // Create message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = marked.parse(content);
        
        // Append avatar and content
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        refreshIcons();
    }
    
    function appendSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i data-lucide="terminal" style="width: 16px; height: 16px;"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        refreshIcons();
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        messageInput.value = '';

        fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        })
        .then(r => r.json())
        .then(data => {
            if (data.response) {
                // Response will come via SSE
            }
        });
    }

    btnSend.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // ===== Image Gallery =====
    function updateGallery(candidates) {
        imageGallery.innerHTML = '';
        candidates.forEach((path, idx) => {
            const card = document.createElement('div');
            card.className = 'image-card';
            card.onclick = () => selectImage(idx);
            
            const img = document.createElement('img');
            img.src = `/api/serve-image?path=${encodeURIComponent(path)}`;
            
            card.appendChild(img);
            imageGallery.appendChild(card);
        });
        refreshIcons();
    }

    function selectImage(index) {
        fetch('/api/images/select', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index})
        })
        .then(r => r.json())
        .then(data => {
            console.log('Image selected:', data);
        });
    }

    // ===== Server-Sent Events =====
    const evtSource = new EventSource('/events');
    
    evtSource.addEventListener("message", (e) => {
        const data = JSON.parse(e.data);
        if (data.role === 'system') {
            appendSystemMessage(data.content);
        } else {
            appendMessage(data.role, data.content);
        }
    });
    
    evtSource.addEventListener("thinking_start", () => {
        thinkingIndicator.classList.remove('hidden');
    });
    
    evtSource.addEventListener("thinking_end", () => {
        thinkingIndicator.classList.add('hidden');
    });
    
    evtSource.addEventListener("image_progress", (e) => {
        const data = JSON.parse(e.data);
        thinkingIndicator.classList.remove('hidden');
        thinkingIndicator.querySelector('.text').textContent = data.status || `Generating image ${data.current}/${data.total}...`;
        
        // Update gallery with current candidates (shows images as they're generated)
        if (data.candidates && data.candidates.length > 0) {
            updateGallery(data.candidates);
        }
        
        // Switch to images view
        switchView('images');
    });

    evtSource.addEventListener("images_ready", (e) => {
        thinkingIndicator.classList.add('hidden');
        thinkingIndicator.querySelector('.text').textContent = "Thinking...";
        const data = JSON.parse(e.data);
        updateGallery(data.candidates);
    });
    
    evtSource.addEventListener("image_selected", (e) => {
        const data = JSON.parse(e.data);
        appendMessage('model', `**Image Saved**: ${data.filename}`);
        imageGallery.innerHTML = '<p class="placeholder">Image saved. Incorporating into presentation...</p>';
    });

    evtSource.addEventListener("tool_start", (e) => {
        const data = JSON.parse(e.data);
        // appendSystemMessage(`🔧 Using tool: ${data.tool}`);
        // Skipping start message to reduce noise, or maybe show a temporary status?
        // For now let's just log it or show it.
        console.log("Tool start:", data);
    });

    evtSource.addEventListener("tool_end", (e) => {
        const data = JSON.parse(e.data);
        // Truncate long results
        let result = data.result || "";
        if (result.length > 200) {
            result = result.substring(0, 200) + "...";
        }
        appendSystemMessage(`✓ Used tool ${data.tool}: ${result}`);
    });

    evtSource.addEventListener("tool_error", (e) => {
        const data = JSON.parse(e.data);
        appendSystemMessage(`✗ Tool ${data.tool} error: ${data.error}`);
    });

    evtSource.addEventListener("presentation_updated", (e) => {
        console.log("Presentation updated, reloading preview...");
        reloadPreview();
        // Switch back to preview view
        switchView('preview');
        // Clear the image gallery
        imageGallery.innerHTML = '<p class="placeholder">No images generated yet.</p>';
    });

    // ===== Initial Load =====
    // Show presentation selector on initial load
    if (presentationSelect) {
        presentationSelect.classList.remove('hidden');
    }
    if (presentationCreate) {
        presentationCreate.classList.add('hidden');
    }
    
    loadPresentationList();
    
    // Initialize icons
    refreshIcons();
});
