document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatHistory = document.getElementById('chat-history');
    const messageInput = document.getElementById('message-input');
    const btnSend = document.getElementById('btn-send');
    const thinkingIndicator = document.getElementById('thinking-indicator');
    const welcomeScreen = document.getElementById('welcome-screen');
    const presentationCreate = document.getElementById('presentation-create');
    const btnCancelCreate = document.getElementById('btn-cancel-create');
    
    // Menu items
    const menuNew = document.getElementById('menu-new');
    const menuOpen = document.getElementById('menu-open');
    const menuClose = document.getElementById('menu-close');
    const menuExport = document.getElementById('menu-export');
    const menuPresSettings = document.getElementById('menu-pres-settings');
    const menuSaveAs = document.getElementById('menu-save-as');
    const menuViewPreview = document.getElementById('menu-view-preview');
    const menuViewLayouts = document.getElementById('menu-view-layouts');
    const menuViewCode = document.getElementById('menu-view-code');
    
    // Sidebar elements
    const viewPreview = document.getElementById('view-preview');
    const previewFrame = document.getElementById('preview-frame');
    
    // Code view elements
    const viewCode = document.getElementById('view-code');
    const fileTree = document.getElementById('file-tree');
    const codeDisplay = document.getElementById('code-display');
    const currentFileName = document.getElementById('current-file-name');
    const saveFileBtn = document.getElementById('save-file-btn');
    const monacoContainer = document.getElementById('monaco-editor-container');
    
    // Monaco editor instance
    let monacoEditor = null;
    let currentFilePath = null;
    let currentFileType = null;
    let hasUnsavedChanges = false;
    const toggleBtnPreview = document.getElementById('toggle-btn-preview');
    const toggleBtnLayouts = document.getElementById('toggle-btn-layouts');
    const toggleBtnCode = document.getElementById('toggle-btn-code');
    
    // Preferences elements
    const preferencesModal = document.getElementById('preferences-modal');
    const prefTheme = document.getElementById('pref-theme');
    const btnSavePreferences = document.getElementById('btn-save-preferences');
    const btnCancelPreferences = document.getElementById('btn-cancel-preferences');
    const menuPreferences = document.getElementById('menu-preferences');
    const menuAbout = document.getElementById('menu-about');
    
    // Presentation Settings elements
    const presSettingsModal = document.getElementById('presentation-settings-modal');
    const presAspectRatio = document.getElementById('pres-aspect-ratio');
    const btnSavePresSettings = document.getElementById('btn-save-pres-settings');
    const btnCancelPresSettings = document.getElementById('btn-cancel-pres-settings');

    // Save As elements
    const saveAsModal = document.getElementById('save-as-modal');
    const saveAsForm = document.getElementById('save-as-form');
    const btnCancelSaveAs = document.getElementById('btn-cancel-save-as');
    
    // Theme buttons
    const themeBtns = document.querySelectorAll('.theme-btn');
    
    // Color theme options
    const colorThemeOptions = document.querySelectorAll('.color-theme-option');
    
    let currentPresName = "";
    let currentColorTheme = "miami"; // Default
    let selectedImageIndex = null; // Track which image candidate is selected
    let currentBatchSlug = null; // Track current image generation batch

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
    
    // ===== Code View Sidebar Resizer =====
    const codeResizer = document.querySelector('.code-resizer');
    const codeSidebar = document.querySelector('.code-sidebar');
    const codeViewContainer = document.querySelector('.code-view-container');
    let isCodeResizing = false;
    let codeStartX = 0;
    let codeStartWidth = 0;
    
    if (codeResizer && codeSidebar && codeViewContainer) {
        codeResizer.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isCodeResizing = true;
            codeStartX = e.clientX;
            codeStartWidth = codeSidebar.offsetWidth;
            
            // Add visual feedback
            codeResizer.classList.add('resizing');
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isCodeResizing) return;
            
            e.preventDefault();
            
            // Calculate new width based on mouse movement
            // Dragging right (increasing clientX) should make sidebar wider
            const dx = e.clientX - codeStartX;
            const newWidth = codeStartWidth + dx;
            
            // Apply constraints
            const minWidth = 200;
            const maxWidth = 600;
            const containerWidth = codeViewContainer.offsetWidth;
            const maxAllowed = Math.min(maxWidth, containerWidth - 300); // Ensure content has at least 300px
            
            if (newWidth >= minWidth && newWidth <= maxAllowed) {
                codeSidebar.style.width = newWidth + 'px';
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isCodeResizing) {
                isCodeResizing = false;
                codeResizer.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
        
        // Handle mouse leaving window during resize
        document.addEventListener('mouseleave', () => {
            if (isCodeResizing) {
                isCodeResizing = false;
                codeResizer.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    // ===== Welcome Screen Functions =====
    function showWelcomeScreen() {
        welcomeScreen.classList.remove('hidden');
        loadPresentationsGrid();
        loadTemplatesGrid();
        refreshIcons();
    }
    
    function hideWelcomeScreen() {
        welcomeScreen.classList.add('hidden');
    }
    
    function loadPresentationsGrid() {
        const grid = document.getElementById('presentations-grid');
        grid.innerHTML = '<div class="slides-preview-loading"><div class="spinner"></div> Loading presentations...</div>';
        
        fetch('/api/presentations')
            .then(r => r.json())
            .then(presentations => {
                grid.innerHTML = '';
                
                // Add "Create New" card first
                const createCard = document.createElement('div');
                createCard.className = 'item-card create-new-card';
                createCard.innerHTML = `
                    <i data-lucide="plus-circle"></i>
                    <span>Create New Presentation</span>
                `;
                createCard.onclick = () => {
                    // Reset to show template selection dropdown
                    document.getElementById('new-pres-template').style.display = '';
                    document.getElementById('template-display').classList.add('hidden');
                    document.getElementById('new-pres-template').value = '';
                    presentationCreate.classList.remove('hidden');
                    loadTemplates();
                };
                grid.appendChild(createCard);
                
                // Add presentation cards
                presentations.forEach(pres => {
                    const card = createPresentationCard(pres);
                    grid.appendChild(card);
                });
                
                refreshIcons();
            })
            .catch(err => {
                console.error('Error loading presentations:', err);
                grid.innerHTML = '<p style="color: hsl(var(--muted-foreground));">Error loading presentations</p>';
            });
    }
    
    function loadTemplatesGrid() {
        const grid = document.getElementById('templates-grid');
        grid.innerHTML = '<div class="slides-preview-loading"><div class="spinner"></div> Loading templates...</div>';
        
        fetch('/api/templates')
            .then(r => r.json())
            .then(templates => {
                grid.innerHTML = '';
                
                if (templates.length === 0) {
                    grid.innerHTML = '<p style="color: hsl(var(--muted-foreground));">No templates available</p>';
                    return;
                }
                
                templates.forEach(template => {
                    const card = createTemplateCard(template);
                    grid.appendChild(card);
                });
                
                refreshIcons();
            })
            .catch(err => {
                console.error('Error loading templates:', err);
                grid.innerHTML = '<p style="color: hsl(var(--muted-foreground));">Error loading templates</p>';
            });
    }
    
    function createPresentationCard(pres) {
        const card = document.createElement('div');
        card.className = 'item-card';
        
        // Format date
        let dateStr = 'Recently';
        if (pres.last_modified) {
            const date = new Date(pres.last_modified);
            const now = new Date();
            const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
            if (diffDays === 0) dateStr = 'Today';
            else if (diffDays === 1) dateStr = 'Yesterday';
            else if (diffDays < 7) dateStr = `${diffDays} days ago`;
            else dateStr = date.toLocaleDateString();
        }
        
        card.innerHTML = `
            <div class="slides-preview">
                <div class="slides-scroll" data-name="${escapeHtml(pres.name)}">
                    <div class="slides-preview-loading">
                        <div class="spinner"></div>
                    </div>
                </div>
            </div>
            <div class="item-info">
                <h3>${escapeHtml(pres.name)}</h3>
                <p class="item-description">${escapeHtml(pres.description || 'No description')}</p>
                <div class="item-meta">
                    <span><i data-lucide="file-text" style="width: 12px; height: 12px;"></i> ${pres.slide_count || 0} slides</span>
                    <span><i data-lucide="clock" style="width: 12px; height: 12px;"></i> ${dateStr}</span>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn-delete">Delete</button>
                <button class="btn-open">Open</button>
            </div>
        `;
        
        // Load preview slides
        const scrollContainer = card.querySelector('.slides-scroll');
        loadSlidePreviewsForPresentation(pres.name, scrollContainer);
        
        // Open button
        card.querySelector('.btn-open').onclick = (e) => {
            e.stopPropagation();
            loadPresentation(pres.name);
        };
        
        // Delete button
        card.querySelector('.btn-delete').onclick = (e) => {
            e.stopPropagation();
            deletePresentation(pres.name);
        };
        
        // Click card to open
        card.onclick = () => {
            loadPresentation(pres.name);
        };
        
        return card;
    }
    
    function createTemplateCard(template) {
        const card = document.createElement('div');
        card.className = 'item-card';
        
        card.innerHTML = `
            <div class="slides-preview">
                <div class="slides-scroll" data-name="${escapeHtml(template.name)}">
                    <div class="slides-preview-loading">
                        <div class="spinner"></div>
                    </div>
                </div>
            </div>
            <div class="item-info">
                <h3>${escapeHtml(template.name)}</h3>
                <p class="item-description">${escapeHtml(template.description || 'No description')}</p>
                <div class="item-meta">
                    <span><i data-lucide="file-text" style="width: 12px; height: 12px;"></i> ${template.slide_count || 0} slides</span>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn-delete">Delete</button>
                <button class="btn-open">Use</button>
            </div>
        `;
        
        // Load preview slides
        const scrollContainer = card.querySelector('.slides-scroll');
        loadSlidePreviewsForTemplate(template.name, scrollContainer);
        
        // Use template button
        card.querySelector('.btn-open').onclick = (e) => {
            e.stopPropagation();
            // Pre-fill template in create modal and show template display
            document.getElementById('new-pres-template').value = template.name;
            document.getElementById('selected-template-name').textContent = template.name;
            document.getElementById('new-pres-template').style.display = 'none';
            document.getElementById('template-display').classList.remove('hidden');
            presentationCreate.classList.remove('hidden');
            loadTemplates();
        };

        // Delete button logic
        card.querySelector('.btn-delete').onclick = (e) => {
            e.stopPropagation();
            deleteTemplate(template.name);
        };
        
        // Click card to use template
        card.onclick = () => {
            document.getElementById('new-pres-template').value = template.name;
            document.getElementById('selected-template-name').textContent = template.name;
            document.getElementById('new-pres-template').style.display = 'none';
            document.getElementById('template-display').classList.remove('hidden');
            presentationCreate.classList.remove('hidden');
            loadTemplates();
        };
        
        return card;
    }
    
    function loadSlidePreviewsForPresentation(name, container) {
        fetch(`/api/presentations/${encodeURIComponent(name)}/preview-slides`)
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    container.innerHTML = '<div class="slides-preview-loading">No preview available</div>';
                    return;
                }
                
                container.innerHTML = '';
                if (data.previews && data.previews.length > 0) {
                    data.previews.forEach(url => {
                        const img = document.createElement('img');
                        img.src = url;
                        img.alt = 'Slide preview';
                        container.appendChild(img);
                    });
                } else {
                    container.innerHTML = '<div class="slides-preview-loading">No slides</div>';
                }
            })
            .catch(err => {
                console.error('Error loading preview slides:', err);
                container.innerHTML = '<div class="slides-preview-loading">Preview unavailable</div>';
            });
    }
    
    function loadSlidePreviewsForTemplate(name, container) {
        fetch(`/api/templates/${encodeURIComponent(name)}/preview-slides`)
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    container.innerHTML = '<div class="slides-preview-loading">No preview available</div>';
                    return;
                }
                
                container.innerHTML = '';
                if (data.previews && data.previews.length > 0) {
                    data.previews.forEach(url => {
                        const img = document.createElement('img');
                        img.src = url;
                        img.alt = 'Slide preview';
                        container.appendChild(img);
                    });
                } else {
                    container.innerHTML = '<div class="slides-preview-loading">No slides</div>';
                }
            })
            .catch(err => {
                console.error('Error loading preview slides:', err);
                container.innerHTML = '<div class="slides-preview-loading">Preview unavailable</div>';
            });
    }
    
    // Welcome screen tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            // Update button states
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content visibility
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`.tab-content[data-tab="${tab}"]`).classList.add('active');
            
            refreshIcons();
        });
    });

    // ===== Menu Handlers =====
    menuNew.addEventListener('click', () => {
        // Reset to show template selection dropdown
        document.getElementById('new-pres-template').style.display = '';
        document.getElementById('template-display').classList.add('hidden');
        document.getElementById('new-pres-template').value = '';
        presentationCreate.classList.remove('hidden');
        loadTemplates();
    });
    
    menuOpen.addEventListener('click', () => {
        showWelcomeScreen();
    });

    if (menuClose) {
        menuClose.addEventListener('click', () => {
            if (!confirm('Are you sure you want to close the current presentation?')) {
                return;
            }
            
            // Close via API
            fetch('/api/state/current-presentation', {
                method: 'DELETE'
            })
            .then(r => r.json())
            .then(data => {
                // Reset UI state
                currentPresName = "";
                chatHistory.innerHTML = '';
                previewFrame.src = '';
                showWelcomeScreen();
            })
            .catch(err => {
                console.error('Error closing presentation:', err);
            });
        });
    }
    
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

    // Presentation Settings Handlers
    if (menuPresSettings) {
        menuPresSettings.addEventListener('click', () => {
            if (!currentPresName) {
                alert('Please open a presentation first.');
                return;
            }
            // Load current settings
            fetch('/api/presentation/settings')
                .then(r => r.json())
                .then(data => {
                    if (data.aspect_ratio) {
                        presAspectRatio.value = data.aspect_ratio;
                    }
                    presSettingsModal.classList.remove('hidden');
                });
        });
    }

    if (btnSavePresSettings) {
        btnSavePresSettings.addEventListener('click', () => {
            const aspectRatio = presAspectRatio.value;
            
            // Show loading state
            appendSystemMessage('Updating aspect ratio and recompiling presentation...');
            
            fetch('/api/presentation/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({aspect_ratio: aspectRatio})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    alert('Error saving settings: ' + data.error);
                    appendSystemMessage('Failed to update aspect ratio.');
                } else {
                    presSettingsModal.classList.add('hidden');
                    appendSystemMessage(`Aspect ratio changed to ${aspectRatio}. Reloading preview...`);
                    // Force reload preview after a brief delay to ensure compilation finished
                    setTimeout(() => {
                        reloadPreview();
                    }, 500);
                }
            })
            .catch(err => {
                alert('Error: ' + err);
                appendSystemMessage('Error updating aspect ratio.');
            });
        });
    }

    if (btnCancelPresSettings) {
        btnCancelPresSettings.addEventListener('click', () => {
            presSettingsModal.classList.add('hidden');
        });
    }

    // Save As Handlers
    if (menuSaveAs) {
        menuSaveAs.addEventListener('click', () => {
            if (!currentPresName) {
                alert('Please open a presentation first.');
                return;
            }
            document.getElementById('save-as-name').value = currentPresName + " Copy";
            saveAsModal.classList.remove('hidden');
        });
    }

    if (saveAsForm) {
        saveAsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const newName = document.getElementById('save-as-name').value;
            const copyImages = document.getElementById('save-as-copy-images').checked;
            
            fetch('/api/presentation/save-as', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: newName, copy_images: copyImages})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    // Success - load the new presentation
                    saveAsModal.classList.add('hidden');
                    loadPresentation(data.name);
                }
            })
            .catch(err => {
                alert('Error: ' + err);
            });
        });
    }

    if (btnCancelSaveAs) {
        btnCancelSaveAs.addEventListener('click', () => {
            saveAsModal.classList.add('hidden');
        });
    }
    
    // ===== View Menu Handlers =====
    
    function switchView(viewName) {
        const allViews = document.querySelectorAll('.sidebar-view');
        const allViewMenuItems = document.querySelectorAll('.dropdown-item.checkable');
        
        // Hide all views
        allViews.forEach(view => view.classList.remove('active'));
        
        // Uncheck all view menu items
        allViewMenuItems.forEach(item => item.classList.remove('active'));
        
        // Show the selected view
        const targetView = document.getElementById(`view-${viewName}`);
        if (targetView) {
            targetView.classList.add('active');
        }
        
        // Check the selected menu item
        const targetMenuItem = document.getElementById(`menu-view-${viewName}`);
        if (targetMenuItem) {
            targetMenuItem.classList.add('active');
        }
        
        // Update view toggle buttons in menu bar
        const allToggleBtns = document.querySelectorAll('.view-toggle-btn');
        allToggleBtns.forEach(btn => btn.classList.remove('active'));
        
        if (viewName === 'preview' && toggleBtnPreview) {
            toggleBtnPreview.classList.add('active');
        } else if (viewName === 'layouts' && toggleBtnLayouts) {
            toggleBtnLayouts.classList.add('active');
        } else if (viewName === 'code' && toggleBtnCode) {
            toggleBtnCode.classList.add('active');
        }
        
        // Save preference
        fetch('/api/preferences/current_view', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({value: viewName})
        }).catch(err => console.error('Error saving view preference:', err));
        
        // If switching to layouts view, load layouts
        if (viewName === 'layouts') {
            loadLayoutsView();
        }
        
        // If switching to code view, load file tree
        if (viewName === 'code') {
            loadCodeView();
        }
        
        // If switching to preview view, reload the preview to show latest changes
        if (viewName === 'preview') {
            reloadPreview();
        }
    }
    
    function createSlideWithLayout(layoutName) {
        // Send message to agent to create a slide with the selected layout
        const message = `Create a new slide using the "${layoutName}" layout.`;
        messageInput.value = message;
        sendMessage();
        
        // Switch to preview view to see the result
        // (The preview will update when presentation_updated event is received)
        switchView('preview');
    }
    
    function loadLayoutsView() {
        fetch('/api/layouts')
            .then(r => r.json())
            .then(data => {
                const accordion = document.getElementById('layouts-accordion');
                if (!accordion) return;
                
                accordion.innerHTML = '';
                
                if (!data.layouts || data.layouts.length === 0) {
                    accordion.innerHTML = '<p>No layouts available</p>';
                    return;
                }
                
                data.layouts.forEach(layout => {
                    const layoutDiv = document.createElement('div');
                    layoutDiv.className = 'layout-item';
                    
                    let badges = '';
                    if (layout.image_friendly) {
                        badges += '<span class="layout-badge image-badge">✓ Image-friendly</span>';
                        if (layout.recommended_aspect_ratio) {
                            badges += `<span class="layout-badge aspect-badge">${escapeHtml(layout.recommended_aspect_ratio)}</span>`;
                        }
                    }
                    
                    layoutDiv.innerHTML = `
                        <h4>${layout.name}</h4>
                        ${layout.description ? `<p class="layout-description">${escapeHtml(layout.description)}</p>` : ''}
                        ${badges}
                        <img class="layout-preview-image" 
                             src="/api/layouts/${encodeURIComponent(layout.name)}/preview" 
                             alt="${escapeHtml(layout.name)} preview"
                             onerror="this.style.display='none'">
                        <div class="layout-actions">
                            <button class="btn-new-slide" data-layout="${escapeHtml(layout.name)}">
                                New Slide
                            </button>
                        </div>
                        <details>
                            <summary>View Code</summary>
                            <pre>${escapeHtml(layout.content)}</pre>
                        </details>
                    `;
                    
                    // Add click handler for New Slide button
                    const newSlideBtn = layoutDiv.querySelector('.btn-new-slide');
                    newSlideBtn.addEventListener('click', () => {
                        createSlideWithLayout(layout.name);
                    });
                    
                    accordion.appendChild(layoutDiv);
                });
            })
            .catch(err => console.error('Error loading layouts:', err));
    }
    
    // ===== Code View Functions =====
    
    function loadCodeView() {
        fetch('/api/presentation/files')
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    console.error('Error loading files:', data.error);
                    return;
                }
                renderFileTree(data.files);
                
                // Auto-open deck.marp.md if nothing is open
                const codeDisplay = document.getElementById('code-display');
                if (codeDisplay && (codeDisplay.innerHTML.trim() === '' || codeDisplay.querySelector('.code-empty-state'))) {
                    function findFileInTree(files, name) {
                        for (const file of files) {
                            if (file.name === name) return file;
                            if (file.children) {
                                const found = findFileInTree(file.children, name);
                                if (found) return found;
                            }
                        }
                        return null;
                    }
                    const mainDeckFile = findFileInTree(data.files, 'deck.marp.md');
                    if (mainDeckFile) {
                        loadFileContent(mainDeckFile.path, mainDeckFile.name, mainDeckFile.type);
                        // Also mark it active in the tree
                        setTimeout(() => {
                            const item = document.querySelector(`.tree-item[data-path="${mainDeckFile.path}"]`);
                            if (item) item.classList.add('active');
                        }, 100);
                    }
                }
            })
            .catch(err => console.error('Error loading file tree:', err));
    }
    
    function renderFileTree(files) {
        if (!fileTree) return;
        
        fileTree.innerHTML = '';
        
        // Sort files by mtime if available (reverse chronological)
        function sortByMtime(items) {
            return items.sort((a, b) => {
                const aTime = (a.mtime ? new Date(a.mtime).getTime() : 0) || 0;
                const bTime = (b.mtime ? new Date(b.mtime).getTime() : 0) || 0;
                // If both have same time or both are 0, maintain original order
                if (aTime === bTime) return 0;
                return bTime - aTime; // Most recent first
            });
        }
        
        // Sort top-level files
        const sortedFiles = sortByMtime([...files]);
        
        sortedFiles.forEach(file => {
            const item = createFileTreeItem(file, 0);
            fileTree.appendChild(item);
        });
        
        // Re-initialize Lucide icons
        lucide.createIcons();
    }
    
    function createFileTreeItem(file, level = 0) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'tree-item-wrapper';
        
        if (file.type === 'folder') {
            // Folder item - shadcn style
            const folderItem = document.createElement('div');
            folderItem.className = 'tree-item folder-item';
            folderItem.dataset.path = file.path;
            folderItem.dataset.type = 'folder';
            
            // Sort children by mtime
            const sortedChildren = file.children ? file.children.sort((a, b) => {
                const aTime = (a.mtime ? new Date(a.mtime).getTime() : 0) || 0;
                const bTime = (b.mtime ? new Date(b.mtime).getTime() : 0) || 0;
                if (aTime === bTime) return 0;
                return bTime - aTime;
            }) : [];
            
            const hasChildren = sortedChildren.length > 0;
            
            folderItem.innerHTML = `
                <div class="tree-item-content">
                    <i class="tree-chevron" data-lucide="chevron-right"></i>
                    <i class="tree-icon" data-lucide="folder"></i>
                    <span class="tree-label">${escapeHtml(file.name)}</span>
                </div>
            `;
            
            itemDiv.appendChild(folderItem);
            
            // Children container
            const childrenDiv = document.createElement('div');
            childrenDiv.className = 'tree-children';
            childrenDiv.style.display = 'none';
            
            if (hasChildren) {
                sortedChildren.forEach(child => {
                    const childItem = createFileTreeItem(child, level + 1);
                    childrenDiv.appendChild(childItem);
                });
            }
            
            itemDiv.appendChild(childrenDiv);
            
            // Toggle expand/collapse
            folderItem.addEventListener('click', (e) => {
                e.stopPropagation();
                const isExpanded = childrenDiv.style.display !== 'none';
                
                if (isExpanded) {
                    childrenDiv.style.display = 'none';
                    folderItem.classList.remove('expanded');
                    const chevron = folderItem.querySelector('.tree-chevron');
                    chevron.setAttribute('data-lucide', 'chevron-right');
                } else {
                    childrenDiv.style.display = 'block';
                    folderItem.classList.add('expanded');
                    const chevron = folderItem.querySelector('.tree-chevron');
                    chevron.setAttribute('data-lucide', 'chevron-down');
                }
                lucide.createIcons();
            });
        } else {
            // File item - shadcn style
            const fileItem = document.createElement('div');
            fileItem.className = 'tree-item file-item';
            fileItem.dataset.path = file.path;
            fileItem.dataset.type = file.type;
            
            // Choose icon based on file type
            let iconName = 'file';
            if (file.type === 'image') {
                iconName = 'image';
            } else if (file.type === 'markdown') {
                iconName = 'file-text';
            } else if (file.type === 'json') {
                iconName = 'braces';
            } else if (file.type === 'code') {
                iconName = 'file-code';
            }
            
            fileItem.innerHTML = `
                <div class="tree-item-content">
                    <i class="tree-icon" data-lucide="${iconName}"></i>
                    <span class="tree-label">${escapeHtml(file.name)}</span>
                </div>
            `;
            
            fileItem.addEventListener('click', (e) => {
                e.stopPropagation();
                loadFileContent(file.path, file.name, file.type);
                
                // Update active state
                document.querySelectorAll('.tree-item').forEach(item => {
                    item.classList.remove('active');
                });
                fileItem.classList.add('active');
            });
            
            itemDiv.appendChild(fileItem);
        }
        
        return itemDiv;
    }
    
    function loadFileContent(path, filename, fileType) {
        if (!currentFileName || !codeDisplay || !monacoContainer) return;
        
        // Check for unsaved changes
        if (hasUnsavedChanges && monacoEditor) {
            if (!confirm('You have unsaved changes. Are you sure you want to switch files?')) {
                return;
            }
        }
        
        currentFilePath = path;
        currentFileType = fileType;
        currentFileName.textContent = filename;
        codeDisplay.innerHTML = '<div class="code-empty-state">Loading...</div>';
        monacoContainer.style.display = 'none';
        if (saveFileBtn) saveFileBtn.style.display = 'none';
        
        // Dispose existing Monaco editor
        if (monacoEditor) {
            monacoEditor.dispose();
            monacoEditor = null;
        }
        
        fetch(`/api/presentation/file-content?path=${encodeURIComponent(path)}`)
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    codeDisplay.innerHTML = `<div class="code-empty-state">Error: ${escapeHtml(data.error)}</div>`;
                    return;
                }
                
                if (data.type === 'image') {
                    // Display image
                    codeDisplay.style.display = 'block';
                    monacoContainer.style.display = 'none';
                    codeDisplay.innerHTML = `<img src="${data.url}" alt="${escapeHtml(filename)}" style="max-width: 100%; height: auto;" />`;
                    if (saveFileBtn) saveFileBtn.style.display = 'none';
                } else if (data.type === 'text') {
                    // Use Monaco editor for text files
                    codeDisplay.style.display = 'none';
                    monacoContainer.style.display = 'block';
                    if (saveFileBtn) saveFileBtn.style.display = 'flex';
                    
                    // Initialize Monaco editor
                    initializeMonacoEditor(data.content, data.language, path);
                } else if (data.type === 'binary') {
                    codeDisplay.style.display = 'block';
                    monacoContainer.style.display = 'none';
                    codeDisplay.innerHTML = `<div class="binary-message">${escapeHtml(data.message)}</div>`;
                    if (saveFileBtn) saveFileBtn.style.display = 'none';
                }
            })
            .catch(err => {
                console.error('Error loading file content:', err);
                codeDisplay.style.display = 'block';
                monacoContainer.style.display = 'none';
                codeDisplay.innerHTML = `<div class="code-empty-state">Error loading file</div>`;
                if (saveFileBtn) saveFileBtn.style.display = 'none';
            });
    }
    
    function initializeMonacoEditor(content, language, filePath) {
        // Check if Monaco is already loaded
        if (typeof monaco !== 'undefined' && monaco.editor) {
            createMonacoEditor(content, language, filePath);
            return;
        }
        
        // Load Monaco editor using the loader
        if (typeof require !== 'undefined') {
            require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
            require(['vs/editor/editor.main'], function () {
                createMonacoEditor(content, language, filePath);
            });
        } else {
            // Fallback: wait a bit for loader to initialize
            setTimeout(() => {
                if (typeof require !== 'undefined') {
                    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
                    require(['vs/editor/editor.main'], function () {
                        createMonacoEditor(content, language, filePath);
                    });
                } else {
                    codeDisplay.style.display = 'block';
                    monacoContainer.style.display = 'none';
                    codeDisplay.innerHTML = '<div class="code-empty-state">Error: Monaco editor failed to load</div>';
                }
            }, 100);
        }
    }
    
    function createMonacoEditor(content, language, filePath) {
        // Determine Monaco language from file extension
        const ext = filePath.split('.').pop().toLowerCase();
        let monacoLanguage = 'plaintext';
        const langMap = {
            'md': 'markdown',
            'markdown': 'markdown',
            'json': 'json',
            'html': 'html',
            'css': 'css',
            'js': 'javascript',
            'py': 'python',
            'yaml': 'yaml',
            'yml': 'yaml'
        };
        if (langMap[ext]) {
            monacoLanguage = langMap[ext];
        } else if (language && language !== 'text') {
            monacoLanguage = language;
        }
        
        // Determine theme based on current theme
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const theme = isDark ? 'vs-dark' : 'vs';
        
        // Create editor
        monacoEditor = monaco.editor.create(monacoContainer, {
            value: content,
            language: monacoLanguage,
            theme: theme,
            lineNumbers: 'on',
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            fontSize: 14,
            wordWrap: 'on'
        });
        
        hasUnsavedChanges = false;
        
        // Track changes
        monacoEditor.onDidChangeModelContent(() => {
            hasUnsavedChanges = true;
            if (saveFileBtn) {
                saveFileBtn.classList.add('has-changes');
            }
        });
    }
    
    function saveFile() {
        if (!monacoEditor || !currentFilePath) return;
        
        const content = monacoEditor.getValue();
        if (!saveFileBtn) return;
        
        // Disable save button and show loading
        saveFileBtn.disabled = true;
        const originalText = saveFileBtn.innerHTML;
        saveFileBtn.innerHTML = '<i data-lucide="loader-2" style="width: 16px; height: 16px;"></i> Saving...';
        lucide.createIcons();
        
        fetch('/api/presentation/file-save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentFilePath, content: content })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert(`Error saving file: ${data.error}`);
                saveFileBtn.disabled = false;
                saveFileBtn.innerHTML = originalText;
                lucide.createIcons();
                return;
            }
            
            hasUnsavedChanges = false;
            saveFileBtn.classList.remove('has-changes');
            
            // Show compile status
            if (data.compile) {
                if (data.compile.success) {
                    saveFileBtn.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i> Saved & Compiled';
                    setTimeout(() => {
                        saveFileBtn.innerHTML = originalText;
                        lucide.createIcons();
                    }, 2000);
                } else {
                    alert(`File saved but compilation failed:\n${data.compile.message}`);
                    saveFileBtn.innerHTML = originalText;
                }
            } else {
                saveFileBtn.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i> Saved';
                setTimeout(() => {
                    saveFileBtn.innerHTML = originalText;
                    lucide.createIcons();
                }, 2000);
            }
            
            saveFileBtn.disabled = false;
            lucide.createIcons();
        })
        .catch(err => {
            console.error('Error saving file:', err);
            alert(`Error saving file: ${err.message}`);
            saveFileBtn.disabled = false;
            saveFileBtn.innerHTML = originalText;
            lucide.createIcons();
        });
    }
    
    // Save button event listener
    if (saveFileBtn) {
        saveFileBtn.addEventListener('click', saveFile);
    }
    
    if (menuViewPreview) {
        menuViewPreview.addEventListener('click', () => switchView('preview'));
    }
    
    if (menuViewLayouts) {
        menuViewLayouts.addEventListener('click', () => switchView('layouts'));
    }
    
    if (menuViewCode) {
        menuViewCode.addEventListener('click', () => switchView('code'));
    }
    
    if (toggleBtnPreview) {
        toggleBtnPreview.addEventListener('click', () => switchView('preview'));
    }
    
    if (toggleBtnLayouts) {
        toggleBtnLayouts.addEventListener('click', () => switchView('layouts'));
    }
    
    if (toggleBtnCode) {
        toggleBtnCode.addEventListener('click', () => switchView('code'));
    }
    
    // Always default to preview view
    // (Saved preferences are not used - preview is the default for better UX)
    switchView('preview');
    
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
    
    if (menuExport) {
        menuExport.addEventListener('click', () => {
            if (!currentPresName) {
                alert('Please open a presentation first.');
                return;
            }
            // Call export endpoint
            appendSystemMessage('Starting PDF export...');
            fetch('/api/presentation/export-pdf', {
                method: 'POST'
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    alert('Error exporting: ' + data.error);
                    appendSystemMessage('Error exporting PDF.');
                } else {
                    alert(data.message);
                    appendSystemMessage('PDF export successful.');
                }
            })
            .catch(err => {
                alert('Error: ' + err);
            });
        });
    }
    
    // Mac-style keyboard shortcut: Cmd+,
    document.addEventListener('keydown', (e) => {
        // Preferences: Cmd/Ctrl + ,
        if ((e.metaKey || e.ctrlKey) && e.key === ',') {
            e.preventDefault();
            openPreferences();
        }
        
        // View shortcuts: Cmd/Ctrl + 1/2/3
        if ((e.metaKey || e.ctrlKey) && e.key === '1') {
            e.preventDefault();
            switchView('preview');
        }
        if ((e.metaKey || e.ctrlKey) && e.key === '2') {
            e.preventDefault();
            switchView('layouts');
        }
        if ((e.metaKey || e.ctrlKey) && e.key === '3') {
            e.preventDefault();
            switchView('code');
        }
    });
    
    if (btnCancelCreate) {
        btnCancelCreate.addEventListener('click', () => {
            presentationCreate.classList.add('hidden');
            // Only show welcome screen if no presentation is loaded
            if (!currentPresName) {
                showWelcomeScreen();
            }
        });
    }

    // Sidebar always shows preview now (no view switching needed)

    function reloadPreview(slideNumber) {
        let url = `/api/presentation/preview?t=${new Date().getTime()}`;
        if (slideNumber) {
            url += `#${slideNumber}`;
        }
        previewFrame.src = url;
    }
    
    // Handle fullscreen toggle for preview
    function togglePreviewFullscreen() {
        console.log('togglePreviewFullscreen called');
        
        // Use the sidebar container for fullscreen (which contains the iframe)
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) {
            console.error('Sidebar not found');
            return;
        }
        
        // Check if we're currently in fullscreen
        const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
        console.log('Current fullscreen state:', isFullscreen);
        
        if (isFullscreen) {
            // Exit fullscreen
            console.log('Exiting fullscreen');
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        } else {
            // Enter fullscreen on the sidebar (which contains the preview)
            console.log('Entering fullscreen on sidebar');
            console.log('requestFullscreen available:', !!sidebar.requestFullscreen);
            console.log('webkitRequestFullscreen available:', !!sidebar.webkitRequestFullscreen);
            
            if (sidebar.requestFullscreen) {
                sidebar.requestFullscreen().then(() => {
                    console.log('Fullscreen entered successfully');
                }).catch(err => {
                    console.error('Error entering fullscreen:', err);
                });
            } else if (sidebar.webkitRequestFullscreen) {
                sidebar.webkitRequestFullscreen();
            } else {
                console.error('Fullscreen API not available');
            }
        }
    }
    
    // Listen for messages from the iframe (Marp controls)
    console.log('[DeckBot] Setting up message listener for Marp controls');
    window.addEventListener('message', (event) => {
        console.log('[DeckBot] Received message:', event.data, 'from origin:', event.origin, 'expected:', window.location.origin);
        
        // Only accept messages from our own origin
        if (event.origin !== window.location.origin) {
            console.log('[DeckBot] Ignoring message from different origin');
            return;
        }
        
        if (event.data && typeof event.data === 'string') {
            console.log('[DeckBot] Processing string message:', event.data);
            // Handle Marp button clicks
            if (event.data === 'marp:fullscreen') {
                console.log('[DeckBot] Fullscreen message received, calling togglePreviewFullscreen()');
                togglePreviewFullscreen();
            } else if (event.data === 'marp:presenter') {
                // Prevent presenter mode from navigating away
                // Just show a message instead
                console.log('[DeckBot] Presenter mode requested');
                alert('Presenter view is not available in DeckBot. Use fullscreen mode instead (F key or fullscreen button).');
            }
        } else {
            console.log('[DeckBot] Ignoring non-string message');
        }
    });
    console.log('[DeckBot] Message listener ready');

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

    // ===== Presentation Delete =====

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
                // Reload the presentations grid
                loadPresentationsGrid();
            }
        })
        .catch(err => {
            alert('Error deleting presentation: ' + err);
        });
    }

    function deleteTemplate(name) {
        if (!confirm(`Are you sure you want to delete template "${name}"?\n\nThis cannot be undone.`)) {
            return;
        }

        fetch('/api/templates/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                // Reload the templates grid
                loadTemplatesGrid();
            }
        })
        .catch(err => {
            alert('Error deleting template: ' + err);
        });
    }

    function handleRichMessage(msg) {
        /**
         * Handle rich message types from chat history.
         * These messages include additional metadata for UI reconstruction.
         */
        const messageType = msg.message_type;
        const data = msg.data;
        
        switch (messageType) {
            case 'image_request_details':
                // Create image request message with details
                const requestDiv = document.createElement('div');
                requestDiv.className = 'message system';
                requestDiv.dataset.batchSlug = data.batch_slug;
                
                const requestAvatar = document.createElement('div');
                requestAvatar.className = 'message-avatar';
                requestAvatar.innerHTML = '<i data-lucide="image" style="width: 16px; height: 16px;"></i>';
                
                const requestContent = document.createElement('div');
                requestContent.className = 'message-content';
                requestContent.innerHTML = `<p><strong>Image:</strong> ${escapeHtml(data.user_message)}</p>`;
                
                requestDiv.appendChild(requestAvatar);
                requestDiv.appendChild(requestContent);
                chatHistory.appendChild(requestDiv);
                
                // Add request details toggle
                addDetailsToggleToMessage(requestDiv, data, 'image');
                refreshIcons();
                break;
                
            case 'image_candidate':
                // Create image candidate message
                appendImageMessage(data.image_path, data.index, data.batch_slug);
                break;
                
            case 'image_selection':
                // Mark the selected image
                const images = chatHistory.querySelectorAll(
                    `.message[data-batch-slug="${data.batch_slug}"] .message-image[data-index="${data.index}"]`
                );
                images.forEach(img => {
                    img.classList.add('selected');
                });
                break;
                
            case 'agent_request_details':
                // Create user message with details attached
                const userMsg = appendMessage('user', data.user_message);
                // Find the just-created message and add details
                const messages = chatHistory.querySelectorAll('.message.user');
                if (messages.length > 0) {
                    const lastUserMessage = messages[messages.length - 1];
                    addDetailsToggleToMessage(lastUserMessage, data, 'agent');
                }
                break;
                
            default:
                console.warn('Unknown message type:', messageType);
        }
    }

    function appendToolUsageMessage(toolName, args, result) {
        /**
         * Create a tool usage message with collapsible details for specific tools.
         * For replace_text, shows filename and collapsible old/new text diff.
         */
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system has-collapsible-content tool-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i data-lucide="wrench" style="width: 16px; height: 16px;"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Main message text
        const mainText = document.createElement('p');
        mainText.className = 'mb-2';
        mainText.textContent = `Used tool ${toolName}`;
        if (args && args.filename) {
            mainText.textContent += `: ${args.filename}`;
        }
        messageContent.appendChild(mainText);
        
        // Tool-specific formatting
        if (toolName === "replace_text" && args) {
            const detailsId = 'tool-details-' + Math.random().toString(36).substr(2, 9);
            
            // Create container for HR, toggle, and content (allows flexbox reordering)
            const toolContainer = document.createElement('div');
            toolContainer.className = 'tool-details-container';
            
            // Create HR (represents collapsed state)
            const hr = document.createElement('hr');
            hr.className = 'tool-details-hr';
            
            // Create toggle button (centered, just caret) - starts at top
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'tool-details-toggle';
            toggleBtn.innerHTML = '<i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>';
            
            // Create details section (content)
            const detailsSection = document.createElement('div');
            detailsSection.className = 'tool-details';
            detailsSection.id = detailsId;
            
            if (args.old_text !== undefined && args.new_text !== undefined) {
                // Old Text section
                const oldHeader = document.createElement('div');
                oldHeader.className = 'tool-detail-header';
                oldHeader.textContent = 'Old Text';
                detailsSection.appendChild(oldHeader);
                
                const oldTextDiv = document.createElement('div');
                oldTextDiv.className = 'tool-detail-content';
                oldTextDiv.textContent = args.old_text;
                detailsSection.appendChild(oldTextDiv);
                
                // New Text section
                const newHeader = document.createElement('div');
                newHeader.className = 'tool-detail-header';
                newHeader.textContent = 'New Text';
                detailsSection.appendChild(newHeader);
                
                const newTextDiv = document.createElement('div');
                newTextDiv.className = 'tool-detail-content';
                newTextDiv.textContent = args.new_text;
                detailsSection.appendChild(newTextDiv);
            }
            
            // Toggle functionality
            let isExpanded = false;
            toggleBtn.onclick = () => {
                isExpanded = !isExpanded;
                
                if (isExpanded) {
                    // Expand: hide HR, show content, move caret to bottom
                    hr.classList.add('hidden');
                    detailsSection.classList.add('expanded');
                    toggleBtn.classList.add('expanded');
                    // Update icon to chevron-up after animation completes
                    setTimeout(() => {
                        if (isExpanded) {
                            toggleBtn.innerHTML = `<i data-lucide="chevron-up" style="width: 14px; height: 14px;"></i>`;
                            refreshIcons();
                        }
                    }, 300); // Match animation duration
                } else {
                    // Collapse: show HR, hide content, move caret to top
                    detailsSection.classList.remove('expanded');
                    toggleBtn.classList.remove('expanded');
                    // Update icon to chevron-down after animation completes
                    setTimeout(() => {
                        if (!isExpanded) {
                            toggleBtn.innerHTML = `<i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>`;
                            refreshIcons();
                            hr.classList.remove('hidden');
                        }
                    }, 300); // Match animation duration
                }
            };
            
            // Initial state: HR visible, content hidden, caret at top
            toolContainer.appendChild(hr);
            toolContainer.appendChild(toggleBtn);
            toolContainer.appendChild(detailsSection);
            messageContent.appendChild(toolContainer);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        refreshIcons();
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
            hideWelcomeScreen();
            
            // Switch to preview view when loading a presentation
            switchView('preview');
            
            // Load preview
            reloadPreview();
            
            // Load chat history
            chatHistory.innerHTML = '';
            if (data.history) {
                data.history.forEach(msg => {
                    // Handle rich message types
                    if (msg.message_type) {
                        handleRichMessage(msg);
                    }
                    // Skip system messages without message_type (old format)
                    else if (msg.role === 'system') {
                        return;
                    }
                    // Handle different part types
                    else if (msg.parts && msg.parts.length > 0) {
                        const part = msg.parts[0];
                        
                        // Text part
                        if (part.text) {
                            appendMessage(msg.role, part.text);
                        }
                        // Function call (tool usage) - display with special formatting
                        else if (part.function_call) {
                            const toolName = part.function_call.name;
                            // Handle both dict objects and JSON strings
                            let args = part.function_call.args || {};
                            if (typeof args === 'string') {
                                try {
                                    args = JSON.parse(args);
                                } catch (e) {
                                    args = {};
                                }
                            }
                            
                            // Use special formatting for replace_text
                            if (toolName === "replace_text" && args && args.filename) {
                                appendToolUsageMessage(toolName, args, null);
                            } else {
                                // Fallback for other tools - format as code block with tool icon
                                const toolCallStr = Object.keys(args).length > 0 ? `${toolName}: ${JSON.stringify(args)}` : toolName;
                                // Create message with tool icon
                                const toolMsgDiv = document.createElement('div');
                                toolMsgDiv.className = 'message system tool-message';
                                
                                const toolAvatar = document.createElement('div');
                                toolAvatar.className = 'message-avatar';
                                toolAvatar.innerHTML = '<i data-lucide="wrench" style="width: 16px; height: 16px;"></i>';
                                
                                const toolContent = document.createElement('div');
                                toolContent.className = 'message-content';
                                toolContent.innerHTML = marked.parse(`Used tool: \`${toolCallStr}\``);
                                
                                toolMsgDiv.appendChild(toolAvatar);
                                toolMsgDiv.appendChild(toolContent);
                                chatHistory.appendChild(toolMsgDiv);
                                chatHistory.scrollTop = chatHistory.scrollHeight;
                                refreshIcons();
                            }
                        }
                        // Function response (tool result) - skip in UI for now
                        else if (part.function_response) {
                            // Skip tool responses in chat display
                        }
                        // Fallback for old format (plain string)
                        else if (typeof part === 'string') {
                            appendMessage(msg.role, part);
                        }
                    }
                    // Old format: content field
                    else if (msg.content) {
                        // Skip [SYSTEM] messages even in old format
                        if (msg.content.startsWith('[SYSTEM]')) {
                            return;
                        }
                        appendMessage(msg.role, msg.content);
                    }
                });
            }
        });
    }

    // ===== Create Presentation =====
    document.getElementById('create-form').addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Disable submit button to prevent double-submission
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.textContent : 'Create';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
        }
        
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
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            } else {
                presentationCreate.classList.add('hidden');
                // Clear form
                document.getElementById('new-pres-name').value = '';
                document.getElementById('new-pres-desc').value = '';
                document.getElementById('new-pres-template').value = '';
                loadPresentation(name);
                
                // Re-enable button after success (ready for next use)
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            }
        })
        .catch(err => {
            console.error('Create presentation error:', err);
            alert('Error creating presentation. See console for details.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
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
        
        return messageDiv;
    }
    
    function appendSystemMessage(title, content = null, isHtml = false, useToolIcon = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        // Add class for tool messages to use normal font
        if (useToolIcon) {
            messageDiv.classList.add('tool-message');
        }
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        if (useToolIcon) {
            avatar.innerHTML = '<i data-lucide="wrench" style="width: 16px; height: 16px;"></i>';
        } else {
            avatar.innerHTML = '<i data-lucide="terminal" style="width: 16px; height: 16px;"></i>';
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (content === null) {
            // Legacy usage: title is the content
            messageContent.textContent = title;
        } else {
            // New usage: title + content
            const titleDiv = document.createElement('div');
            titleDiv.className = 'font-medium mb-1';
            titleDiv.textContent = title;
            messageContent.appendChild(titleDiv);
            
            const contentDiv = document.createElement('div');
            if (isHtml) {
                contentDiv.innerHTML = content;
            } else {
                contentDiv.textContent = content;
            }
            messageContent.appendChild(contentDiv);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        refreshIcons();
    }

    function appendImageMessage(imagePath, index, batchSlug) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.dataset.imageIndex = index;
        messageDiv.dataset.batchSlug = batchSlug;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i data-lucide="image" style="width: 16px; height: 16px;"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const imageWrapper = document.createElement('div');
        imageWrapper.className = 'message-image';
        imageWrapper.dataset.index = index;
        
        const img = document.createElement('img');
        img.src = `/api/serve-image?path=${encodeURIComponent(imagePath)}`;
        img.alt = `Candidate ${index + 1}`;
        
        imageWrapper.appendChild(img);
        imageWrapper.onclick = () => selectImageCandidate(index, imageWrapper);
        
        messageContent.appendChild(imageWrapper);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        refreshIcons();
    }

    function selectImageCandidate(index, imageElement) {
        // Mark this image as selected visually
        document.querySelectorAll('.message-image').forEach(img => {
            img.classList.remove('selected');
        });
        imageElement.classList.add('selected');
        selectedImageIndex = index;
        
        // Send selection to backend
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

    function createRequestDetailsSection(details, requestType) {
        const detailsDiv = document.createElement('div');
        // Use same class structure as tool details for consistent styling
        detailsDiv.className = 'request-details tool-details-content';
        
        if (requestType === 'image') {
            // Don't show user prompt in details since it's already visible in the message
            detailsDiv.innerHTML = `
                <div class="detail-section">
                    <div class="detail-label">System Instructions</div>
                    <div class="detail-content">${escapeHtml(details.system_message)}</div>
                </div>
                <div class="detail-section">
                    <div class="detail-meta">
                        <div class="detail-meta-item">
                            <i data-lucide="maximize" style="width: 14px; height: 14px;"></i>
                            <span>${details.aspect_ratio}</span>
                        </div>
                        <div class="detail-meta-item">
                            <i data-lucide="monitor" style="width: 14px; height: 14px;"></i>
                            <span>${details.resolution}</span>
                        </div>
                    </div>
                </div>
            `;
        } else if (requestType === 'agent') {
            let metaHtml = '';
            if (details.model) {
                metaHtml = `
                    <div class="detail-section">
                        <div class="detail-meta">
                            <div class="detail-meta-item">
                                <i data-lucide="cpu" style="width: 14px; height: 14px;"></i>
                                <span>${escapeHtml(details.model)}</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            detailsDiv.innerHTML = `
                <div class="detail-section">
                    <div class="detail-label">User Message</div>
                    <div class="detail-content">${escapeHtml(details.user_message)}</div>
                </div>
                <div class="detail-section">
                    <div class="detail-label">System Prompt</div>
                    <div class="detail-content">${escapeHtml(details.system_prompt)}</div>
                </div>
                ${metaHtml}
            `;
        }
        
        refreshIcons();
        return detailsDiv;
    }

    function addDetailsToggleToMessage(messageDiv, details, requestType) {
        // Find message content
        let messageContent = messageDiv.querySelector('.message-content');
        if (!messageContent) return;
        
        // Add class to mark this message as having collapsible content
        messageDiv.classList.add('has-collapsible-content');
        
        // Create container for HR, toggle, and details (same pattern as tool messages)
        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'tool-details-container';
        
        // Create HR (represents collapsed state)
        const hr = document.createElement('hr');
        hr.className = 'tool-details-hr';
        
        // Create toggle button (centered, just caret) - starts at top
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'tool-details-toggle';
        toggleBtn.innerHTML = '<i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>';
        
        // Create details section (content)
        const detailsSection = createRequestDetailsSection(details, requestType);
        // Add tool-details class for collapsible behavior, keep request-details for styling
        detailsSection.classList.add('tool-details');
        
        // Toggle functionality
        let isExpanded = false;
        toggleBtn.onclick = () => {
            isExpanded = !isExpanded;
            
            // Update icon by completely replacing innerHTML
            const newIconName = isExpanded ? 'chevron-up' : 'chevron-down';
            toggleBtn.innerHTML = `<i data-lucide="${newIconName}" style="width: 14px; height: 14px;"></i>`;
            refreshIcons();
            
            if (isExpanded) {
                // Expand: hide HR, show content, move caret to bottom
                hr.classList.add('hidden');
                detailsSection.classList.add('expanded');
                toggleBtn.classList.add('expanded');
                // Update icon after animation
                setTimeout(() => {
                    if (isExpanded) {
                        toggleBtn.innerHTML = `<i data-lucide="chevron-up" style="width: 14px; height: 14px;"></i>`;
                        refreshIcons();
                    }
                }, 300);
            } else {
                // Collapse: show HR, hide content, move caret to top
                detailsSection.classList.remove('expanded');
                toggleBtn.classList.remove('expanded');
                // Update icon after animation
                setTimeout(() => {
                    if (!isExpanded) {
                        toggleBtn.innerHTML = `<i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>`;
                        refreshIcons();
                        hr.classList.remove('hidden');
                    }
                }, 300);
            }
        };
        
        // Initial state: HR visible, content hidden, caret at top
        detailsContainer.appendChild(hr);
        detailsContainer.appendChild(toggleBtn);
        detailsContainer.appendChild(detailsSection);
        messageContent.appendChild(detailsContainer);
        refreshIcons();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Don't append immediately - let it come through SSE
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


    // ===== Server-Sent Events =====
    // ===== Layout Selection Dialog =====
    
    function showLayoutSelectionDialog(layouts, title, position) {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        overlay.style.display = 'flex';
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal layout-selection-modal';
        
        const titleText = title ? ` titled "${title}"` : '';
        modal.innerHTML = `
            <h2>Select a Layout</h2>
            <p>Creating a new slide${titleText}. Choose a layout:</p>
            <div class="layouts-grid"></div>
            <div class="modal-actions">
                <button class="btn-cancel">Cancel</button>
            </div>
        `;
        
        const layoutsGrid = modal.querySelector('.layouts-grid');
        
        // Add layout options
        layouts.forEach(layout => {
            const layoutCard = document.createElement('div');
            layoutCard.className = 'layout-card';
            
            // Create simple preview (just show the layout name and first few lines)
            const previewLines = layout.content.split('\\n').slice(0, 5).join('\\n');
            
            // Build metadata badges
            let metadataHtml = '';
            if (layout.description) {
                metadataHtml += `<div class="layout-description">${escapeHtml(layout.description)}</div>`;
            }
            if (layout.image_friendly) {
                metadataHtml += `<span class="layout-badge image-badge">✓ Image-friendly</span>`;
                if (layout.recommended_aspect_ratio) {
                    metadataHtml += `<span class="layout-badge aspect-badge">${escapeHtml(layout.recommended_aspect_ratio)}</span>`;
                }
            }
            
            layoutCard.innerHTML = `
                <div class="layout-name">${layout.name}</div>
                ${metadataHtml}
                <div class="layout-preview">
                    <pre>${escapeHtml(previewLines)}...</pre>
                </div>
                <button class="btn-select-layout" data-layout="${escapeHtml(layout.name)}">
                    Select
                </button>
            `;
            
            layoutsGrid.appendChild(layoutCard);
        });
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Handle selection
        modal.querySelectorAll('.btn-select-layout').forEach(btn => {
            btn.addEventListener('click', async () => {
                const layoutName = btn.dataset.layout;
                
                try {
                    const response = await fetch('/api/layouts/select', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({layout_name: layoutName})
                    });
                    
                    if (response.ok) {
                        document.body.removeChild(overlay);
                    } else {
                        const error = await response.json();
                        alert('Error: ' + (error.error || 'Failed to select layout'));
                    }
                } catch (err) {
                    alert('Error selecting layout: ' + err.message);
                }
            });
        });
        
        // Handle cancel
        modal.querySelector('.btn-cancel').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });
    }
    
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
        // Scroll to bottom to ensure thinking indicator is visible and doesn't overlay user message
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
    
    evtSource.addEventListener("thinking_end", () => {
        thinkingIndicator.classList.add('hidden');
    });
    
    evtSource.addEventListener("image_request_details", (e) => {
        const data = JSON.parse(e.data);
        // Store batch slug for this generation
        currentBatchSlug = data.batch_slug;
        
        // Create a system message showing the user prompt and generating status
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.dataset.batchSlug = data.batch_slug;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i data-lucide="image" style="width: 16px; height: 16px;"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        // Show user prompt by default, with "Generating..." status
        messageContent.innerHTML = `<p><strong>Image:</strong> ${escapeHtml(data.user_message)}</p><p class="text-muted">Generating images...</p>`;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Add request details to this message (system instructions will be in collapsed section)
        addDetailsToggleToMessage(messageDiv, data, 'image');
        refreshIcons();
    });

    evtSource.addEventListener("image_candidate", (e) => {
        const data = JSON.parse(e.data);
        appendImageMessage(data.image_path, data.index, data.batch_slug);
    });

    evtSource.addEventListener("image_progress", (e) => {
        const data = JSON.parse(e.data);
        thinkingIndicator.classList.remove('hidden');
        thinkingIndicator.querySelector('.text').textContent = data.status || `Generating image ${data.current}/${data.total}...`;
    });

    evtSource.addEventListener("images_ready", (e) => {
        thinkingIndicator.classList.add('hidden');
        thinkingIndicator.querySelector('.text').textContent = "Thinking...";
    });
    
    evtSource.addEventListener("image_selected", (e) => {
        const data = JSON.parse(e.data);
        appendSystemMessage(`Image saved: ${data.filename}`);
    });

    evtSource.addEventListener("agent_request_details", (e) => {
        const data = JSON.parse(e.data);
        // Find the most recent user message and add details to it
        const messages = chatHistory.querySelectorAll('.message.user');
        if (messages.length > 0) {
            const lastUserMessage = messages[messages.length - 1];
            addDetailsToggleToMessage(lastUserMessage, data, 'agent');
        }
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
        let result = data.result || "";
        
        // Check for Visual QA delimiter
        const visualQaDelimiter = "---VISUAL_QA_START---";
        let visualQaReport = null;
        
        if (result.includes(visualQaDelimiter)) {
            const parts = result.split(visualQaDelimiter);
            result = parts[0]; // The main tool output
            visualQaReport = parts[1]; // The Visual QA report
        }
        
        // --- Handle Main Tool Output ---
        
        // Special handling for replace_text
        if (data.tool === "replace_text" && data.args) {
            appendToolUsageMessage(data.tool, data.args, result);
        } else {
            // Truncate long results, but make them expandable
            let content = result;
            let needsExpand = false;
            
            if (data.tool === "read_file") {
                // Special compact mode for read_file
                const summary = `File content loaded (${result.length} characters).`;
                const safeResult = escapeHtml(result).replace(/\n/g, '<br>');
                
                const id = 'tool-res-' + Math.random().toString(36).substr(2, 9);
                
                content = `
                    <div class="tool-result-summary text-muted">${escapeHtml(summary)}</div>
                    <button class="text-link" onclick="document.getElementById('${id}').classList.toggle('hidden')">Show Full Output</button>
                    <div id="${id}" class="tool-result-full hidden mt-2 p-2 bg-muted rounded text-xs font-mono whitespace-pre-wrap">${safeResult}</div>
                `;
                
                needsExpand = true; // Treats content as HTML
                
            } else if (result.length > 200) {
                // Create a summary
                const summary = result.substring(0, 200) + "...";
                // Create a details section
                const safeResult = escapeHtml(result).replace(/\n/g, '<br>');
                
                const id = 'tool-res-' + Math.random().toString(36).substr(2, 9);
                
                content = `
                    <div class="tool-result-summary">${escapeHtml(summary)}</div>
                    <button class="text-link" onclick="document.getElementById('${id}').classList.toggle('hidden')">Show Full Output</button>
                    <div id="${id}" class="tool-result-full hidden mt-2 p-2 bg-muted rounded text-xs font-mono whitespace-pre-wrap">${safeResult}</div>
                `;
                
                needsExpand = true;
            }
            
            // Format tool name and args as code block
            const toolCallStr = data.args ? `${data.tool}: ${JSON.stringify(data.args)}` : data.tool;
            appendSystemMessage(`Used tool: \`${toolCallStr}\``, content, needsExpand, true); // true = use tool icon
        }
        
        // --- Handle Visual QA Report (Separate Message) ---
        if (visualQaReport) {
            // Parse important parts
            let isCritical = visualQaReport.includes("CRITICAL VISUAL ISSUES FOUND");
            let description = "";
            let verdict = "";
            
            // Extract Description
            const descMatch = visualQaReport.match(/DESCRIPTION:(.*?)(?:VERDICT:|$)/s);
            if (descMatch) description = descMatch[1].trim();
            
            // Extract Verdict
            const verdictMatch = visualQaReport.match(/VERDICT:(.*?)(?:STOP AND THINK:|$)/s);
            if (verdictMatch) verdict = verdictMatch[1].trim();
            
            // Is it clean?
            if (verdict.includes("No issues found")) {
                // Maybe don't show prominent warning, just a checkmark?
                // User said: "We want to see the explanation... and the flag... always see that"
            }
            
            // Build HTML for Visual QA Message
            // Header
            let icon = isCritical ? '<i data-lucide="alert-triangle" class="text-red-500" style="width: 16px; height: 16px;"></i>' : '<i data-lucide="check-circle" class="text-green-500" style="width: 16px; height: 16px;"></i>';
            let title = isCritical ? "Visual Inspection: Issues Detected" : "Visual Inspection: Passed";
            
            let reportHtml = `
                <div class="visual-qa-report ${isCritical ? 'critical' : 'passed'}">
                    <div class="qa-summary mb-2">
                        ${description ? `<p class="mb-1"><strong>Observed:</strong> ${escapeHtml(description)}</p>` : ''}
                        ${verdict ? `<p class="mb-1"><strong>Verdict:</strong> ${escapeHtml(verdict)}</p>` : ''}
                    </div>
            `;
            
            // Expandable Details (Full Report)
            const qaId = 'qa-res-' + Math.random().toString(36).substr(2, 9);
            
            // Clean up the report for raw view - remove the redundant header that we already show in UI
            let cleanReport = visualQaReport;
            if (isCritical) {
                cleanReport = cleanReport.replace(/CRITICAL VISUAL ISSUES FOUND:\s*/, '');
            }
            cleanReport = cleanReport.trim();
            
            const safeReport = escapeHtml(cleanReport).replace(/\n/g, '<br>');
            
            reportHtml += `
                    <button class="text-link text-xs" onclick="document.getElementById('${qaId}').classList.toggle('hidden')">View Full Report</button>
                    <div id="${qaId}" class="tool-result-full hidden mt-2 p-2 bg-muted rounded text-xs font-mono whitespace-pre-wrap">${safeReport}</div>
                </div>
            `;
            
            // Append as a separate system message with special styling
            // We use a custom function or just appendSystemMessage with HTML
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system visual-qa-message';
            if (isCritical) messageDiv.classList.add('border-l-4', 'border-red-500', 'bg-red-50/10', 'pl-3');
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.innerHTML = '<i data-lucide="eye" style="width: 16px; height: 16px;"></i>';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            const titleDiv = document.createElement('div');
            titleDiv.className = `font-medium mb-1 flex items-center gap-2 ${isCritical ? 'text-red-500' : 'text-green-500'}`;
            titleDiv.innerHTML = `${icon} ${title}`;
            messageContent.appendChild(titleDiv);
            
            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = reportHtml;
            messageContent.appendChild(contentDiv);
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            
            chatHistory.appendChild(messageDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            refreshIcons();
        }
    });

    evtSource.addEventListener("tool_error", (e) => {
        const data = JSON.parse(e.data);
        appendSystemMessage(`✗ Tool ${data.tool} error: ${data.error}`);
    });

    evtSource.addEventListener("layout_request", (e) => {
        const data = JSON.parse(e.data);
        showLayoutSelectionDialog(data.layouts, data.title, data.position);
    });

    evtSource.addEventListener("presentation_updated", (e) => {
        console.log("Presentation updated, reloading preview...");
        
        // Automatically switch to preview view when presentation is updated
        switchView('preview');
        
        // Check if event data contains slide number
        let slideNumber = null;
        try {
            if (e.data) {
                const data = JSON.parse(e.data);
                if (data && data.slide_number) {
                    slideNumber = data.slide_number;
                }
            }
        } catch (err) {
            console.warn("Error parsing presentation_updated data", err);
        }
        
        reloadPreview(slideNumber);
    });

    // ===== Initial Load =====
    
    // Check for persisted state first
    fetch('/api/state/current-presentation')
        .then(r => r.json())
        .then(state => {
            if (state.name) {
                // Auto-restore presentation
                console.log('Restoring session for:', state.name);
                loadPresentation(state.name);
                
                // Ensure welcome screen is hidden
                hideWelcomeScreen();
                if (presentationCreate) {
                    presentationCreate.classList.add('hidden');
                }
            } else {
                // No state, show welcome screen
                showWelcomeScreen();
                if (presentationCreate) {
                    presentationCreate.classList.add('hidden');
                }
            }
        })
        .catch(err => {
            console.error('Error checking state:', err);
            // Fallback to welcome screen
            showWelcomeScreen();
        });
    
    // Initialize icons
    refreshIcons();
});
