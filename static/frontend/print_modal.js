// Print Modal Functionality
class PrintModal {
    constructor() {
        this.selectedCards = [];
        this.availableCards = [];
        this.modal = null;
        this.init();
    }

    init() {
        // Create modal HTML
        this.createModal();
        // Setup event listeners
        this.setupEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div id="printModalOverlay" class="print-modal-overlay">
                <div class="print-modal">
                    <div class="print-modal-header">
                        <h2>Print Dashboard</h2>
                        <button class="print-modal-close" type="button">&times;</button>
                    </div>
                    <div class="print-modal-body">
                        <div class="print-modal-left">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <h3 style="margin: 0;">Available Cards</h3>
                                <button id="selectAllCardsBtn" class="btn-select-all" type="button" title="Select all cards">
                                    <i class="bi bi-check-square"></i> Select All
                                </button>
                            </div>
                            <div class="card-thumbnail-list" id="availableCardsList">
                                <!-- Cards will be populated here -->
                            </div>
                        </div>
                        <div class="print-modal-right">
                            <h3>Selected Cards (Drag to reorder)</h3>
                            <div class="selected-cards-container" id="selectedCardsContainer">
                                <div class="empty-state">
                                    <i class="bi bi-inbox"></i>
                                    <p>No cards selected. Drag cards from the left to add them.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="print-modal-footer">
                        <button class="btn-cancel" type="button">Cancel</button>
                        <div class="print-btn-group">
                            <button class="print-btn-primary" type="button" id="printBtn">
                                <i class="bi bi-printer"></i> Print
                            </button>
                            <button class="print-btn-dropdown" type="button" id="printDropdownBtn">
                                <i class="bi bi-chevron-down"></i>
                            </button>
                            <div class="print-dropdown-menu" id="printDropdownMenu">
                                <div class="print-dropdown-item" data-action="print">
                                    <i class="bi bi-printer"></i> Print
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('printModalOverlay');
    }

    setupEventListeners() {
        // Close button
        const closeBtn = this.modal.querySelector('.print-modal-close');
        const cancelBtn = this.modal.querySelector('.btn-cancel');
        
        closeBtn.addEventListener('click', () => this.close());
        cancelBtn.addEventListener('click', () => this.close());
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Print dropdown
        const dropdownBtn = this.modal.querySelector('#printDropdownBtn');
        const dropdownMenu = this.modal.querySelector('#printDropdownMenu');
        
        dropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = dropdownMenu.classList.toggle('active');
            dropdownBtn.classList.toggle('active', isActive);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('active');
                dropdownBtn.classList.remove('active');
            }
        });

        // Dropdown items
        dropdownMenu.querySelectorAll('.print-dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action;
                dropdownMenu.classList.remove('active');
                dropdownBtn.classList.remove('active');
                if (action === 'print') {
                    this.print();
                } else if (action === 'download') {
                    this.downloadPDF();
                }
            });
        });

        // Print button
        const printBtn = this.modal.querySelector('#printBtn');
        printBtn.addEventListener('click', () => this.print());
        
        // Select All button
        const selectAllBtn = this.modal.querySelector('#selectAllCardsBtn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllAvailableCards();
            });
        }
    }

    // Convert Chart.js canvas to image
    async convertChartToImage(canvas) {
        return new Promise((resolve) => {
            if (!canvas) {
                resolve(null);
                return;
            }
            
            try {
                // Try to get Chart.js instance
                let chart = null;
                if (typeof Chart !== 'undefined') {
                    // Chart.js v3+ uses Chart.getChart()
                    if (Chart.getChart) {
                        chart = Chart.getChart(canvas);
                    }
                    // Chart.js v2 uses canvas.chart
                    if (!chart && canvas.chart) {
                        chart = canvas.chart;
                    }
                }
                
                if (chart && typeof chart.toBase64Image === 'function') {
                    // Get the chart as base64 image
                    const imageUrl = chart.toBase64Image();
                    const img = document.createElement('img');
                    img.src = imageUrl;
                    img.style.maxWidth = '100%';
                    img.style.height = 'auto';
                    img.style.display = 'block';
                    resolve(img);
                } else {
                    // If no chart instance, try to get canvas as image directly
                    // Wait a bit for canvas to render
                    setTimeout(() => {
                        try {
                            const imageUrl = canvas.toDataURL('image/png', 1.0);
                            const img = document.createElement('img');
                            img.src = imageUrl;
                            img.style.maxWidth = '100%';
                            img.style.height = 'auto';
                            img.style.display = 'block';
                            resolve(img);
                        } catch (error) {
                            console.warn('Error converting canvas to image:', error);
                            resolve(null);
                        }
                    }, 100);
                }
            } catch (error) {
                console.warn('Error converting chart to image:', error);
                // Fallback: try canvas toDataURL
                try {
                    const imageUrl = canvas.toDataURL('image/png', 1.0);
                    const img = document.createElement('img');
                    img.src = imageUrl;
                    img.style.maxWidth = '100%';
                    img.style.height = 'auto';
                    img.style.display = 'block';
                    resolve(img);
                } catch (e) {
                    resolve(null);
                }
            }
        });
    }

    // Process element to convert charts and capture data
    async processElementForPrint(element) {
        // Clone the original element to get structure
        const processed = element.cloneNode(true);
        
        // Find all canvas elements (Chart.js charts) - need to find them in original first
        const originalCanvases = element.querySelectorAll('canvas');
        const processedCanvases = processed.querySelectorAll('canvas');
        
        // Convert each canvas to image
        for (let i = 0; i < originalCanvases.length; i++) {
            const originalCanvas = originalCanvases[i];
            const processedCanvas = processedCanvases[i];
            
            if (originalCanvas && processedCanvas) {
                const img = await this.convertChartToImage(originalCanvas);
                if (img) {
                    // Replace canvas with image
                    const parent = processedCanvas.parentElement;
                    if (parent) {
                        // Hide the canvas
                        processedCanvas.style.display = 'none';
                        // Insert image after canvas
                        parent.insertBefore(img, processedCanvas.nextSibling);
                    }
                }
            }
        }

        // Update all dynamic content from original element
        const updateElementContent = (origEl, procEl) => {
            if (!origEl || !procEl) return;
            
            // Update text content for leaf nodes
            if (origEl.children.length === 0 && procEl.children.length === 0) {
                if (origEl.textContent !== procEl.textContent) {
                    procEl.textContent = origEl.textContent;
                }
                if (origEl.innerHTML !== procEl.innerHTML) {
                    procEl.innerHTML = origEl.innerHTML;
                }
            }
            
            // Update attributes that might contain data
            Array.from(origEl.attributes).forEach(attr => {
                if (attr.name !== 'id' && attr.name !== 'class') {
                    procEl.setAttribute(attr.name, attr.value);
                }
            });
            
            // Recursively update children
            if (origEl.children && procEl.children) {
                for (let i = 0; i < Math.min(origEl.children.length, procEl.children.length); i++) {
                    updateElementContent(origEl.children[i], procEl.children[i]);
                }
            }
        };

        // Update the entire structure
        updateElementContent(element, processed);

        // Specifically update key data elements that might have been dynamically updated
        const dataSelectors = [
            '.value', '.stat-info h3', '[id^="stat-"]', 
            '.text-center.text-muted', '.timeline-item',
            'tbody tr', '.rank-item', '.coop-name', '.coop-asset',
            '.gender-count', '.status-pill', '.badge-status',
            'td', 'th', '.card-content', '.stat-info',
            '.label', 'p.label', '.stat-info p', 'h3.value'
        ];
        
        dataSelectors.forEach(selector => {
            const originalElements = element.querySelectorAll(selector);
            const processedElements = processed.querySelectorAll(selector);
            
            originalElements.forEach((origEl, index) => {
                if (processedElements[index]) {
                    // Update text and HTML
                    if (origEl.textContent !== processedElements[index].textContent) {
                        processedElements[index].textContent = origEl.textContent;
                    }
                    if (origEl.innerHTML !== processedElements[index].innerHTML) {
                        processedElements[index].innerHTML = origEl.innerHTML;
                    }
                    // Update classes (for status badges, etc.)
                    if (origEl.className !== processedElements[index].className) {
                        processedElements[index].className = origEl.className;
                    }
                }
            });
        });
        
        // Special handling for stat cards - ensure all content is updated
        if (element.classList.contains('stat-card')) {
            const origStatInfo = element.querySelector('.stat-info, .card-content');
            const procStatInfo = processed.querySelector('.stat-info, .card-content');
            
            if (origStatInfo && procStatInfo) {
                // Update all children
                Array.from(origStatInfo.children).forEach((origChild, index) => {
                    const procChild = procStatInfo.children[index];
                    if (procChild) {
                        procChild.textContent = origChild.textContent;
                        procChild.innerHTML = origChild.innerHTML;
                        procChild.className = origChild.className;
                    }
                });
            }
        }

        // Handle loading states - replace with actual content
        const loadingSelectors = ['.text-center.text-muted', '[class*="loading"]'];
        loadingSelectors.forEach(selector => {
            const processedLoading = processed.querySelectorAll(selector);
            const originalLoading = element.querySelectorAll(selector);
            
            processedLoading.forEach((procEl, index) => {
                if (originalLoading[index]) {
                    const text = procEl.textContent.trim();
                    const origText = originalLoading[index].textContent.trim();
                    
                    if ((text.includes('Loading') || text.includes('loading') || text === '...') && 
                        !origText.includes('Loading') && origText !== '...') {
                        procEl.textContent = origText;
                        procEl.innerHTML = originalLoading[index].innerHTML;
                    }
                }
            });
        });

        return processed;
    }

    // Get a selector for an element (for finding original)
    getElementSelector(element) {
        if (element.id) return `#${element.id}`;
        if (element.className) {
            const classes = Array.from(element.classList).join('.');
            const tag = element.tagName.toLowerCase();
            return `${tag}.${classes}`;
        }
        return null;
    }

    extractCardsFromDashboard() {
        const cards = [];
        const dashboardContainer = document.querySelector('.admin-dashboard-container, .staff-dashboard-container, .coop-dashboard-container');
        
        if (!dashboardContainer) return cards;

        // Track processed elements to avoid duplicates
        const processed = new Set();

        // Helper function to check if element is already processed
        const isProcessed = (el) => {
            return processed.has(el) || Array.from(processed).some(processedEl => processedEl.contains(el) || el.contains(processedEl));
        };

        // Helper function to mark as processed
        const markProcessed = (el) => {
            processed.add(el);
        };

        // Helper function to get card title
        const getCardTitle = (el) => {
            // For stat cards, prioritize the label
            if (el.classList.contains('stat-card')) {
                // Try .label first (cooperative dashboard style)
                const labelEl = el.querySelector('.label, p.label');
                if (labelEl) {
                    return labelEl.textContent.trim();
                }
                // Try .stat-info p (staff/admin dashboard style)
                const statInfoLabel = el.querySelector('.stat-info > p:first-child, .card-content > p.label:first-child');
                if (statInfoLabel) {
                    return statInfoLabel.textContent.trim();
                }
                // Try any p that's not in small or span
                const pLabel = el.querySelector('.stat-info p:not(small p), .card-content p:not(small p)');
                if (pLabel && !pLabel.classList.contains('text-muted')) {
                    return pLabel.textContent.trim();
                }
            }
            
            // For other cards, try headers first
            const titleEl = el.querySelector('h3, h2, h4, .card-header-custom h3, .section-header h3, .card-header-custom h2');
            if (titleEl) {
                return titleEl.textContent.trim();
            }
            
            // Then try labels
            const labelEl = el.querySelector('.label, p.label, .stat-info p, .subtitle');
            if (labelEl) {
                return labelEl.textContent.trim();
            }
            
            return null;
        };

        // Helper function to get preview text
        const getPreview = (el) => {
            // For stat cards, get the value and description
            if (el.classList.contains('stat-card')) {
                const valueEl = el.querySelector('.value, h3, .stat-info h3');
                const descEl = el.querySelector('.text-muted, small, .stat-info small');
                let preview = '';
                if (valueEl) {
                    preview = valueEl.textContent.trim();
                }
                if (descEl && descEl.textContent.trim()) {
                    preview += (preview ? ' • ' : '') + descEl.textContent.trim();
                }
                return preview || '';
            }
            
            // For other cards
            const previewEl = el.querySelector('.text-muted, small, .stat-info small');
            if (previewEl) {
                return previewEl.textContent.trim();
            }
            return '';
        };

        // 1. Extract stat cards (KPI cards)
        const statCards = dashboardContainer.querySelectorAll('.stat-card');
        statCards.forEach((el, index) => {
            if (isProcessed(el)) return;
            markProcessed(el);
            
            // Get title - prioritize label for stat cards
            let title = getCardTitle(el);
            if (!title) {
                // Fallback: try to get any text that looks like a label
                const firstP = el.querySelector('.stat-info > p:first-child, .card-content > p:first-child, .stat-info p, .card-content p');
                if (firstP && !firstP.classList.contains('text-muted')) {
                    title = firstP.textContent.trim();
                }
            }
            if (!title) {
                title = `Stat Card ${index + 1}`;
            }
            
            const preview = getPreview(el);
            
            // Clone with deep copy to include all data
            const cloned = el.cloneNode(true);
            
            cards.push({
                id: `stat-${Date.now()}-${index}`,
                title: title,
                preview: preview,
                element: cloned,
                originalElement: el
            });
        });

        // 2. Extract chart cards
        const chartCards = dashboardContainer.querySelectorAll('.chart-card, .card-section');
        chartCards.forEach((el, index) => {
            if (isProcessed(el)) return;
            markProcessed(el);
            
            const title = getCardTitle(el) || `Chart ${index + 1}`;
            
            // Clone with deep copy
            const cloned = el.cloneNode(true);
            
            cards.push({
                id: `chart-${Date.now()}-${index}`,
                title: title,
                preview: '',
                element: cloned,
                originalElement: el
            });
        });

        // 3. Extract dashboard sections
        const sections = dashboardContainer.querySelectorAll('.dashboard-section');
        sections.forEach((section, index) => {
            if (isProcessed(section)) return;
            
            // Skip if section only contains cards we've already processed
            const hasUnprocessedCards = Array.from(section.querySelectorAll('.stat-card, .chart-card, .card-section'))
                .some(card => !isProcessed(card));
            
            if (!hasUnprocessedCards && section.querySelector('.stat-card, .chart-card, .card-section')) {
                return; // Skip sections that only contain already processed cards
            }
            
            markProcessed(section);
            
            const title = getCardTitle(section) || `Section ${index + 1}`;
            
            // Clone with deep copy
            const cloned = section.cloneNode(true);
            
            cards.push({
                id: `section-${Date.now()}-${index}`,
                title: title,
                preview: '',
                element: cloned,
                originalElement: section
            });
        });

        // 4. Extract hero cards and special cards
        const heroCards = dashboardContainer.querySelectorAll('.hero-card, .dashboard-card');
        heroCards.forEach((el, index) => {
            if (isProcessed(el)) return;
            markProcessed(el);
            
            const title = getCardTitle(el) || `Card ${index + 1}`;
            
            // Clone with deep copy
            const cloned = el.cloneNode(true);
            
            cards.push({
                id: `hero-${Date.now()}-${index}`,
                title: title,
                preview: '',
                element: cloned,
                originalElement: el
            });
        });

        // 5. Extract content splits (side-by-side sections)
        const contentSplits = dashboardContainer.querySelectorAll('.content-split > div');
        contentSplits.forEach((el, index) => {
            if (isProcessed(el)) return;
            markProcessed(el);
            
            const title = getCardTitle(el) || `Content Section ${index + 1}`;
            
            // Clone with deep copy
            const cloned = el.cloneNode(true);
            
            cards.push({
                id: `split-${Date.now()}-${index}`,
                title: title,
                preview: '',
                element: cloned,
                originalElement: el
            });
        });

        return cards;
    }

    async open() {
        // Show loading state
        const leftContainer = this.modal.querySelector('#availableCardsList');
        const rightContainer = this.modal.querySelector('#selectedCardsContainer');
        leftContainer.innerHTML = '<div class="empty-state"><i class="bi bi-hourglass-split"></i><p>Loading cards...</p></div>';
        rightContainer.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>No cards selected. Drag cards from the left to add them.</p></div>';
        
        // Show modal first
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Extract cards from dashboard
        this.availableCards = this.extractCardsFromDashboard();
        this.selectedCards = [];
        
        // Process cards to convert charts to images
        for (let i = 0; i < this.availableCards.length; i++) {
            const card = this.availableCards[i];
            card.element = await this.processElementForPrint(card.originalElement);
        }
        
        // Render available cards
        this.renderAvailableCards();
        this.renderSelectedCards();
    }

    close() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        
        // Close dropdown if open
        const dropdownMenu = this.modal.querySelector('#printDropdownMenu');
        const dropdownBtn = this.modal.querySelector('#printDropdownBtn');
        if (dropdownMenu) {
            dropdownMenu.classList.remove('active');
        }
        if (dropdownBtn) {
            dropdownBtn.classList.remove('active');
        }
        
        // Clear selections after a delay to allow animation
        setTimeout(() => {
            this.selectedCards = [];
            this.availableCards = [];
        }, 300);
    }

    renderAvailableCards() {
        const container = this.modal.querySelector('#availableCardsList');
        const selectAllBtn = this.modal.querySelector('#selectAllCardsBtn');
        container.innerHTML = '';

        // Filter out already selected cards
        const available = this.availableCards.filter(card => 
            !this.selectedCards.find(selected => selected.id === card.id)
        );

        if (available.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-check-circle"></i><p>All cards selected</p></div>';
            // Disable select all button
            if (selectAllBtn) {
                selectAllBtn.disabled = true;
                selectAllBtn.style.opacity = '0.5';
            }
            return;
        }

        // Enable select all button
        if (selectAllBtn) {
            selectAllBtn.disabled = false;
            selectAllBtn.style.opacity = '1';
        }

        available.forEach(card => {
            const cardEl = this.createThumbnailCard(card);
            container.appendChild(cardEl);
        });
    }

    createThumbnailCard(card) {
        const div = document.createElement('div');
        div.className = 'card-thumbnail';
        div.draggable = true;
        div.dataset.cardId = card.id;
        
        // Get current preview from original element with actual values
        let preview = card.preview;
        if (card.originalElement) {
            // For stat cards, show the actual value
            if (card.originalElement.classList.contains('stat-card')) {
                const valueEl = card.originalElement.querySelector('.value, h3, .stat-info h3');
                const descEl = card.originalElement.querySelector('.text-muted, small, .stat-info small');
                let previewParts = [];
                if (valueEl) {
                    previewParts.push(valueEl.textContent.trim());
                }
                if (descEl && descEl.textContent.trim()) {
                    previewParts.push(descEl.textContent.trim());
                }
                preview = previewParts.join(' • ');
            } else {
                const previewEl = card.originalElement.querySelector('.text-muted, small, .stat-info small, .value');
                if (previewEl) {
                    preview = previewEl.textContent.trim();
                }
            }
        }
        
        div.innerHTML = `
            <div class="card-thumbnail-title">${card.title || 'Card'}</div>
            ${preview ? `<div class="card-thumbnail-preview">${preview}</div>` : ''}
        `;

        // Drag start
        div.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', card.id);
            div.classList.add('dragging');
        });

        div.addEventListener('dragend', () => {
            div.classList.remove('dragging');
        });

        // Click to add
        div.addEventListener('click', () => {
            this.addCard(card.id);
        });

        return div;
    }

    async renderSelectedCards() {
        const container = this.modal.querySelector('#selectedCardsContainer');
        container.innerHTML = '';

        if (this.selectedCards.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>No cards selected. Drag cards from the left to add them.</p></div>';
            return;
        }

        // Process and render each card
        for (let i = 0; i < this.selectedCards.length; i++) {
            const card = this.selectedCards[i];
            const cardEl = await this.createSelectedCard(card, i);
            container.appendChild(cardEl);
        }

        // Setup drag and drop for reordering
        this.setupDragAndDrop();
    }

    async createSelectedCard(card, index) {
        const div = document.createElement('div');
        div.className = 'selected-card-item';
        div.draggable = true;
        div.dataset.cardId = card.id;
        div.dataset.index = index;
        
        // Process the card element to ensure charts are converted
        const processedElement = await this.processElementForPrint(card.originalElement);
        
        div.innerHTML = `
            <button class="selected-card-remove" type="button" title="Remove card">&times;</button>
            <div class="selected-card-content">
                ${processedElement.outerHTML}
            </div>
        `;

        // Remove button
        const removeBtn = div.querySelector('.selected-card-remove');
        removeBtn.addEventListener('click', () => {
            this.removeCard(card.id);
        });

        // Drag for reordering
        div.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', card.id);
            e.dataTransfer.effectAllowed = 'move';
            div.classList.add('dragging');
        });

        div.addEventListener('dragend', () => {
            div.classList.remove('dragging');
        });

        div.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        div.addEventListener('drop', (e) => {
            e.preventDefault();
            const draggedId = e.dataTransfer.getData('text/plain');
            this.reorderCard(draggedId, index);
        });

        return div;
    }

    setupDragAndDrop() {
        const container = this.modal.querySelector('#selectedCardsContainer');
        const availableContainer = this.modal.querySelector('#availableCardsList');

        // Allow dropping from available to selected
        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        container.addEventListener('drop', (e) => {
            e.preventDefault();
            const cardId = e.dataTransfer.getData('text/plain');
            if (cardId && !this.selectedCards.find(c => c.id === cardId)) {
                this.addCard(cardId);
            }
        });

        // Allow dropping from selected to available (remove)
        availableContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        availableContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            const cardId = e.dataTransfer.getData('text/plain');
            if (cardId) {
                this.removeCard(cardId);
            }
        });
    }

    async addCard(cardId) {
        const card = this.availableCards.find(c => c.id === cardId);
        if (card && !this.selectedCards.find(c => c.id === cardId)) {
            // Process the card element to ensure it has all data
            const processedCard = {
                ...card,
                element: await this.processElementForPrint(card.originalElement)
            };
            this.selectedCards.push(processedCard);
            this.renderAvailableCards();
            await this.renderSelectedCards();
        }
    }

    async selectAllAvailableCards() {
        // Get all available cards (not yet selected)
        const available = this.availableCards.filter(card => 
            !this.selectedCards.find(selected => selected.id === card.id)
        );

        if (available.length === 0) {
            return; // No cards to select
        }

        // Show loading state
        const selectAllBtn = this.modal.querySelector('#selectAllCardsBtn');
        const originalText = selectAllBtn.innerHTML;
        selectAllBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Adding...';
        selectAllBtn.disabled = true;

        try {
            // Process and add all available cards
            for (const card of available) {
                const processedCard = {
                    ...card,
                    element: await this.processElementForPrint(card.originalElement)
                };
                this.selectedCards.push(processedCard);
            }

            // Update UI
            this.renderAvailableCards();
            await this.renderSelectedCards();
        } catch (error) {
            console.error('Error selecting all cards:', error);
        } finally {
            selectAllBtn.innerHTML = originalText;
            selectAllBtn.disabled = false;
        }
    }

    removeCard(cardId) {
        this.selectedCards = this.selectedCards.filter(c => c.id !== cardId);
        this.renderAvailableCards();
        this.renderSelectedCards();
    }

    reorderCard(cardId, newIndex) {
        const cardIndex = this.selectedCards.findIndex(c => c.id === cardId);
        if (cardIndex === -1) return;

        const card = this.selectedCards.splice(cardIndex, 1)[0];
        this.selectedCards.splice(newIndex, 0, card);
        this.renderSelectedCards();
    }

    async print() {
        if (this.selectedCards.length === 0) {
            alert('Please select at least one card to print.');
            return;
        }

        // Show loading
        const printBtn = this.modal.querySelector('#printBtn');
        const originalText = printBtn.innerHTML;
        printBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Preparing...';
        printBtn.disabled = true;

        try {
            // Create print window
            const printWindow = window.open('', '_blank');
            const printContent = await this.generatePrintContent();
            
            printWindow.document.write(printContent);
            printWindow.document.close();
            
            // Wait for content to load, then print
            printWindow.onload = () => {
                setTimeout(() => {
                    printWindow.print();
                    printBtn.innerHTML = originalText;
                    printBtn.disabled = false;
                }, 500);
            };
        } catch (error) {
            console.error('Print error:', error);
            alert('Error preparing print. Please try again.');
            printBtn.innerHTML = originalText;
            printBtn.disabled = false;
        }
    }

    async downloadPDF() {
        if (this.selectedCards.length === 0) {
            alert('Please select at least one card to download.');
            return;
        }

        // Check if html2pdf is available
        if (typeof html2pdf === 'undefined') {
            alert('PDF download is not available. Please use the print option instead.');
            return;
        }

        // Show loading
        const downloadItem = this.modal.querySelector('[data-action="download"]');
        const originalText = downloadItem.innerHTML;
        downloadItem.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating PDF...';

        try {
            // Create a temporary container with processed content
            const tempContainer = document.createElement('div');
            tempContainer.style.position = 'absolute';
            tempContainer.style.left = '-9999px';
            tempContainer.className = 'print-content-area';
            
            // Process all cards and add to container
            for (const card of this.selectedCards) {
                const processed = await this.processElementForPrint(card.originalElement);
                const cardDiv = document.createElement('div');
                cardDiv.style.marginBottom = '20px';
                cardDiv.style.pageBreakInside = 'avoid';
                cardDiv.appendChild(processed);
                tempContainer.appendChild(cardDiv);
            }
            
            document.body.appendChild(tempContainer);

            const opt = {
                margin: 0.5,
                filename: `dashboard-${new Date().toISOString().split('T')[0]}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { 
                    scale: 2, 
                    useCORS: true,
                    logging: false,
                    allowTaint: true
                },
                jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
            };

            await html2pdf().set(opt).from(tempContainer).save();
            
            document.body.removeChild(tempContainer);
            downloadItem.innerHTML = originalText;
        } catch (err) {
            console.error('PDF generation error:', err);
            const tempContainer = document.querySelector('.print-content-area');
            if (tempContainer) {
                document.body.removeChild(tempContainer);
            }
            downloadItem.innerHTML = originalText;
            alert('Error generating PDF. Please try again.');
        }
    }

    async generatePrintContent() {
        // Process all selected cards to ensure charts are converted
        const processedCards = [];
        for (const card of this.selectedCards) {
            const processed = await this.processElementForPrint(card.originalElement);
            processedCards.push(processed);
        }

        const cardsHTML = processedCards.map(card => {
            return `<div class="selected-card-item" style="page-break-inside: avoid; margin-bottom: 20px;">
                ${card.outerHTML}
            </div>`;
        }).join('');

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Dashboard Print</title>
                <style>
                    @page {
                        margin: 1cm;
                    }
                    body {
                        font-family: 'Inter', sans-serif;
                        color: #2B3674;
                        padding: 20px;
                    }
                    .selected-card-item {
                        page-break-inside: avoid;
                        margin-bottom: 20px;
                        padding: 16px;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                    }
                    img {
                        max-width: 100%;
                        height: auto;
                    }
                    canvas {
                        display: none;
                    }
                    @media print {
                        .selected-card-item {
                            page-break-inside: avoid;
                        }
                    }
                </style>
            </head>
            <body>
                ${cardsHTML}
            </body>
            </html>
        `;
    }
}

// Initialize print modal when DOM is ready
let printModalInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    printModalInstance = new PrintModal();
    
    // Make it globally accessible
    window.printModal = printModalInstance;
});




