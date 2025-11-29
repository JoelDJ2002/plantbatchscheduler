// Global configuration object
let config = {
    equipment: [],
    products: [
        {
            "id": "A",
            "name": "Product-A",
            "batch_size": 100,
            "recipe": [
                {"step_name": "Reaction", "equipment_type": "Reactor", "duration": 4.0},
                {"step_name": "Drying", "equipment_type": "Dryer", "duration": 8.0},
                {"step_name": "Packaging", "equipment_type": "Packager", "duration": 2.0},
            ]
        },
        {
            "id": "B",
            "name": "Product-B",
            "batch_size": 80,
            "recipe": [
                {"step_name": "Reaction", "equipment_type": "Reactor", "duration": 6.0},
                {"step_name": "Drying", "equipment_type": "Dryer", "duration": 6.0},
                {"step_name": "Packaging", "equipment_type": "Packager", "duration": 1.5},
            ]
        },
        {
            "id": "C",
            "name": "Product-C",
            "batch_size": 120,
            "recipe": [
                {"step_name": "Reaction", "equipment_type": "Reactor", "duration": 3.0},
                {"step_name": "Drying", "equipment_type": "Dryer", "duration": 10.0},
                {"step_name": "Packaging", "equipment_type": "Packager", "duration": 2.5},
            ]
        },
    ],
    changeovers: [],
    orders: [],
    hours_per_day: 24,
    simulation_time_days: 30
};

// Track available IDs for each equipment type to reuse when possible
let availableIds = {
    'Reactor': new Set(),
    'Dryer': new Set(),
    'Packager': new Set()
};

// DOM elements
const equipmentList = document.getElementById('equipment-list');
const ordersList = document.getElementById('orders-list');
const changeoversList = document.getElementById('changeovers-list');
const simulationDaysInput = document.getElementById('simulation-days');
const resultsSection = document.getElementById('results');
const resultsContent = document.getElementById('results-content');
const aiAnalysisSection = document.getElementById('ai-analysis');
const aiAnalysisContent = document.getElementById('ai-analysis-content');
const sidebar = document.getElementById('sidebar');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupSidebar();
    setupEventListeners();
    loadDefaultData();
    updateSidebarCounts();
});

// Sidebar functionality
function setupSidebar() {
    // Toggle sidebar collapse
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Section collapse/expand
    const sectionHeaders = document.querySelectorAll('.nav-section-header');
    sectionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.nav-section');
            section.classList.toggle('collapsed');
            header.classList.toggle('active');
        });
    });

    // Navigation buttons
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });

    // Sidebar run simulation button
    const runSimSidebar = document.getElementById('run-simulation-sidebar');
    if (runSimSidebar) {
        runSimSidebar.addEventListener('click', runSimulation);
    }
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Update active section in sidebar
    const sectionHeaders = document.querySelectorAll('.nav-section-header');
    sectionHeaders.forEach(header => {
        const section = header.closest('.nav-section');
        const sectionName = header.dataset.section;
        if (sectionName === tabName) {
            section.classList.remove('collapsed');
            header.classList.add('active');
        } else {
            header.classList.remove('active');
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Equipment
    document.getElementById('add-equipment').addEventListener('click', addEquipment);

    // Orders
    document.getElementById('add-order').addEventListener('click', addOrder);

    // Changeovers
    document.getElementById('add-changeover').addEventListener('click', addChangeover);

    // Simulation
    document.getElementById('run-simulation').addEventListener('click', runSimulation);
    document.getElementById('save-config').addEventListener('click', saveConfiguration);

    // Update simulation days
    simulationDaysInput.addEventListener('input', () => {
        updateSimulationDays();
        updateSidebarCounts();
    });

    // Close results
    const closeResults = document.getElementById('close-results');
    if (closeResults) {
        closeResults.addEventListener('click', () => {
            resultsSection.classList.add('hidden');
        });
    }

    // AI Analysis
    const analyzeAiBtn = document.getElementById('analyze-ai');
    if (analyzeAiBtn) {
        analyzeAiBtn.addEventListener('click', runAIAnalysis);
    }

    // Close AI analysis
    const closeAiAnalysis = document.getElementById('close-ai-analysis');
    if (closeAiAnalysis) {
        closeAiAnalysis.addEventListener('click', () => {
            aiAnalysisSection.classList.add('hidden');
        });
    }
}

// Update sidebar counts and summaries
function updateSidebarCounts() {
    // Equipment counts
    const reactorCount = config.equipment.filter(eq => eq.type === 'Reactor').length;
    const dryerCount = config.equipment.filter(eq => eq.type === 'Dryer').length;
    const packagerCount = config.equipment.filter(eq => eq.type === 'Packager').length;
    const totalEquipment = config.equipment.length;

    document.getElementById('equipment-count').textContent = totalEquipment;
    document.getElementById('reactor-count').textContent = reactorCount;
    document.getElementById('dryer-count').textContent = dryerCount;
    document.getElementById('packager-count').textContent = packagerCount;

    // Orders counts
    const totalOrders = config.orders.length;
    const totalQuantity = config.orders.reduce((sum, order) => sum + order.quantity, 0);

    document.getElementById('orders-count').textContent = totalOrders;
    document.getElementById('total-orders').textContent = totalOrders;
    document.getElementById('total-quantity').textContent = `${totalQuantity} kg`;

    // Changeovers count
    document.getElementById('changeovers-count').textContent = config.changeovers.length;
    document.getElementById('defined-changeovers').textContent = config.changeovers.length;

    // Simulation duration
    document.getElementById('sim-duration').textContent = `${config.simulation_time_days} days`;
}

// Load default data
function loadDefaultData() {
    // Load default equipment
    const defaultEquipment = [
        {"id": "R-101", "type": "Reactor", "capacity": 500},
        {"id": "R-102", "type": "Reactor", "capacity": 500},
        {"id": "D-201", "type": "Dryer", "capacity": 200},
        {"id": "P-301", "type": "Packager", "capacity": 100},
    ];

    defaultEquipment.forEach(eq => {
        config.equipment.push(eq);
        renderEquipmentItem(eq);
        // Mark these IDs as used (not available for recycling)
        const number = parseInt(eq.id.split('-')[1]);
        if (!isNaN(number)) {
            availableIds[eq.type].delete(number);
        }
    });

    // Load default orders
    const defaultOrders = [
        {"id": "1", "product_id": "A", "quantity": 1000, "due_date": 1, "priority": 2},
        {"id": "2", "product_id": "B", "quantity": 800, "due_date": 4, "priority": 2},
        {"id": "3", "product_id": "C", "quantity": 1200, "due_date": 5, "priority": 4},
        {"id": "4", "product_id": "A", "quantity": 600, "due_date": 3, "priority": 1},
        {"id": "5", "product_id": "B", "quantity": 500, "due_date": 2, "priority": 3},
        {"id": "6", "product_id": "C", "quantity": 400, "due_date": 6, "priority": 2},
    ];

    defaultOrders.forEach(order => {
        config.orders.push(order);
        renderOrderItem(order);
    });

    // Load default changeovers
    const defaultChangeovers = [
        {"from_product": "A", "to_product": "B", "time": 4.0},
        {"from_product": "A", "to_product": "C", "time": 6.0},
        {"from_product": "B", "to_product": "A", "time": 5.0},
        {"from_product": "B", "to_product": "C", "time": 3.0},
        {"from_product": "C", "to_product": "A", "time": 8.0},
        {"from_product": "C", "to_product": "B", "time": 4.0},
    ];

    defaultChangeovers.forEach(co => {
        config.changeovers.push(co);
        renderChangeoverItem(co);
    });

    updateSidebarCounts();
}

// Equipment management
function addEquipment() {
    const equipmentItem = {
        id: generateEquipmentId('Reactor'),
        type: 'Reactor',
        capacity: 500
    };

    config.equipment.push(equipmentItem);
    renderEquipmentItem(equipmentItem);
    updateSidebarCounts();
}

function renderEquipmentItem(equipment) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'equipment-item';
    itemDiv.dataset.id = equipment.id;
    itemDiv.innerHTML = `
        <div class="item-header">
            <div class="item-title">Equipment ${equipment.id}</div>
            <button class="delete-btn" onclick="deleteEquipment('${equipment.id}')">Delete</button>
        </div>
        <div class="equipment-grid">
            <div class="form-group">
                <label>Type:</label>
                <select onchange="updateEquipmentType('${equipment.id}', this.value)">
                    <option value="Reactor" ${equipment.type === 'Reactor' ? 'selected' : ''}>Reactor</option>
                    <option value="Dryer" ${equipment.type === 'Dryer' ? 'selected' : ''}>Dryer</option>
                    <option value="Packager" ${equipment.type === 'Packager' ? 'selected' : ''}>Packager</option>
                </select>
            </div>
            <div class="form-group">
                <label>Capacity:</label>
                <input type="number" value="${equipment.capacity}" min="1"
                       onchange="updateEquipmentCapacity('${equipment.id}', this.value)">
            </div>
        </div>
    `;
    equipmentList.appendChild(itemDiv);
}

function deleteEquipment(id) {
    const equipment = config.equipment.find(eq => eq.id === id);
    if (equipment) {
        const number = parseInt(id.split('-')[1]);
        if (!isNaN(number)) {
            availableIds[equipment.type].add(number);
        }

        config.equipment = config.equipment.filter(eq => eq.id !== id);
        refreshEquipmentList();
        updateSidebarCounts();
    }
}

function updateEquipmentType(id, newType) {
    const equipment = config.equipment.find(eq => eq.id === id);
    if (equipment) {
        const oldType = equipment.type;

        if (oldType !== newType) {
            const currentNumber = parseInt(id.split('-')[1]);
            if (!isNaN(currentNumber)) {
                availableIds[oldType].add(currentNumber);
            }

            equipment.type = newType;
            equipment.id = generateEquipmentId(newType);
        }

        refreshEquipmentList();
        updateSidebarCounts();
    }
}

function updateEquipmentCapacity(id, newCapacity) {
    const equipment = config.equipment.find(eq => eq.id === id);
    if (equipment) {
        equipment.capacity = parseFloat(newCapacity);
    }
}

function generateEquipmentId(type) {
    const prefix = type === 'Reactor' ? 'R' : type === 'Dryer' ? 'D' : 'P';

    if (availableIds[type].size > 0) {
        const recycledId = Math.min(...availableIds[type]);
        availableIds[type].delete(recycledId);
        return `${prefix}-${recycledId}`;
    }

    const existingIds = config.equipment
        .filter(eq => eq.type === type)
        .map(eq => parseInt(eq.id.split('-')[1]))
        .filter(id => !isNaN(id));

    let number = 101;
    while (existingIds.includes(number)) {
        number++;
    }

    return `${prefix}-${number}`;
}

function refreshEquipmentList() {
    equipmentList.innerHTML = '';
    config.equipment.forEach(eq => renderEquipmentItem(eq));
}

// Orders management
function addOrder() {
    const maxId = config.orders.reduce((max, order) => {
        const id = parseInt(order.id);
        return isNaN(id) ? max : Math.max(max, id);
    }, 0);
    
    const nextId = (maxId + 1).toString();
    const orderItem = {
        id: nextId,
        product_id: 'A',
        quantity: 1000,
        due_date: 1,
        priority: Math.floor(Math.random() * 4) + 1
    };

    config.orders.push(orderItem);
    renderOrderItem(orderItem);
    updateSidebarCounts();
}

function renderOrderItem(order) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'order-item';
    itemDiv.dataset.id = order.id;
    itemDiv.innerHTML = `
        <div class="item-header">
            <div class="item-title">Order #${order.id}</div>
            <button class="delete-btn" onclick="deleteOrder('${order.id}')">Delete</button>
        </div>
        <div class="order-grid">
            <div class="form-group">
                <label>Product:</label>
                <select onchange="updateOrderProduct('${order.id}', this.value)">
                    <option value="A" ${order.product_id === 'A' ? 'selected' : ''}>Product A</option>
                    <option value="B" ${order.product_id === 'B' ? 'selected' : ''}>Product B</option>
                    <option value="C" ${order.product_id === 'C' ? 'selected' : ''}>Product C</option>
                </select>
            </div>
            <div class="form-group">
                <label>Quantity (kg):</label>
                <input type="number" value="${order.quantity}" min="1"
                       onchange="updateOrderQuantity('${order.id}', this.value)">
            </div>
            <div class="form-group">
                <label>Due Date (days):</label>
                <input type="number" value="${order.due_date}" min="1"
                       onchange="updateOrderDueDate('${order.id}', this.value)">
            </div>
            <div class="form-group">
                <label>Priority (1-4):</label>
                <input type="number" value="${order.priority}" min="1" max="4"
                       onchange="updateOrderPriority('${order.id}', this.value)">
            </div>
        </div>
    `;
    ordersList.appendChild(itemDiv);
}

function deleteOrder(id) {
    config.orders = config.orders.filter(order => order.id !== id);
    refreshOrdersList();
    updateSidebarCounts();
}

function updateOrderProduct(id, newProduct) {
    const order = config.orders.find(o => o.id === id);
    if (order) {
        order.product_id = newProduct;
    }
}

function updateOrderQuantity(id, newQuantity) {
    const order = config.orders.find(o => o.id === id);
    if (order) {
        order.quantity = parseInt(newQuantity);
        updateSidebarCounts();
    }
}

function updateOrderDueDate(id, newDueDate) {
    const order = config.orders.find(o => o.id === id);
    if (order) {
        order.due_date = parseInt(newDueDate);
    }
}

function updateOrderPriority(id, newPriority) {
    const order = config.orders.find(o => o.id === id);
    if (order) {
        order.priority = parseInt(newPriority);
    }
}

function refreshOrdersList() {
    ordersList.innerHTML = '';
    config.orders.forEach(order => renderOrderItem(order));
}

// Changeover management
function addChangeover() {
    const changeoverItem = {
        from_product: 'A',
        to_product: 'B',
        time: 4.0
    };

    config.changeovers.push(changeoverItem);
    renderChangeoverItem(changeoverItem);
    updateSidebarCounts();
}

function renderChangeoverItem(changeover) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'changeover-item';
    itemDiv.innerHTML = `
        <div class="item-header">
            <div class="item-title">Changeover ${changeover.from_product} → ${changeover.to_product}</div>
            <button class="delete-btn" onclick="deleteChangeover('${changeover.from_product}-${changeover.to_product}')">Delete</button>
        </div>
        <div class="changeover-grid">
            <div class="form-group">
                <label>From Product:</label>
                <select onchange="updateChangeoverFrom('${changeover.from_product}-${changeover.to_product}', this.value)">
                    <option value="A" ${changeover.from_product === 'A' ? 'selected' : ''}>Product A</option>
                    <option value="B" ${changeover.from_product === 'B' ? 'selected' : ''}>Product B</option>
                    <option value="C" ${changeover.from_product === 'C' ? 'selected' : ''}>Product C</option>
                </select>
            </div>
            <div class="form-group">
                <label>To Product:</label>
                <select onchange="updateChangeoverTo('${changeover.from_product}-${changeover.to_product}', this.value)">
                    <option value="A" ${changeover.to_product === 'A' ? 'selected' : ''}>Product A</option>
                    <option value="B" ${changeover.to_product === 'B' ? 'selected' : ''}>Product B</option>
                    <option value="C" ${changeover.to_product === 'C' ? 'selected' : ''}>Product C</option>
                </select>
            </div>
            <div class="form-group">
                <label>Time (hours):</label>
                <input type="number" value="${changeover.time}" min="0" step="0.5"
                       onchange="updateChangeoverTime('${changeover.from_product}-${changeover.to_product}', this.value)">
            </div>
        </div>
    `;
    changeoversList.appendChild(itemDiv);
}

function deleteChangeover(id) {
    const [from, to] = id.split('-');
    config.changeovers = config.changeovers.filter(co => !(co.from_product === from && co.to_product === to));
    refreshChangeoversList();
    updateSidebarCounts();
}

function updateChangeoverFrom(id, newFrom) {
    const [oldFrom, oldTo] = id.split('-');
    const changeover = config.changeovers.find(co => co.from_product === oldFrom && co.to_product === oldTo);
    if (changeover) {
        // Prevent same from and to
        if (newFrom === changeover.to_product) {
            alert('From and To products cannot be the same!');
            refreshChangeoversList();
            return;
        }
        changeover.from_product = newFrom;
        refreshChangeoversList();
    }
}

function updateChangeoverTo(id, newTo) {
    const [oldFrom, oldTo] = id.split('-');
    const changeover = config.changeovers.find(co => co.from_product === oldFrom && co.to_product === oldTo);
    if (changeover) {
        // Prevent same from and to
        if (newTo === changeover.from_product) {
            alert('From and To products cannot be the same!');
            refreshChangeoversList();
            return;
        }
        changeover.to_product = newTo;
        refreshChangeoversList();
    }
}

function updateChangeoverTime(id, newTime) {
    const [from, to] = id.split('-');
    const changeover = config.changeovers.find(co => co.from_product === from && co.to_product === to);
    if (changeover) {
        changeover.time = parseFloat(newTime);
    }
}

function refreshChangeoversList() {
    changeoversList.innerHTML = '';
    config.changeovers.forEach(co => renderChangeoverItem(co));
}

// Simulation settings
function updateSimulationDays() {
    config.simulation_time_days = parseInt(simulationDaysInput.value);
}

// Save configuration
function saveConfiguration() {
    config.simulation_time_days = parseInt(simulationDaysInput.value);

    const finalConfig = {
        equipment: config.equipment,
        products: config.products,
        changeovers: config.changeovers,
        orders: config.orders,
        hours_per_day: config.hours_per_day,
        simulation_time_days: config.simulation_time_days
    };

    localStorage.setItem('plantConfig', JSON.stringify(finalConfig, null, 2));

    const dataStr = JSON.stringify(finalConfig, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'plant_config.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    alert('Configuration saved as plant_config.json');
}

// Run simulation
async function runSimulation() {
    const runBtn = document.getElementById('run-simulation');
    const runBtnSidebar = document.getElementById('run-simulation-sidebar');
    
    try {
        // Show loading state
        const originalText = runBtn.innerHTML;
        const originalSidebarText = runBtnSidebar ? runBtnSidebar.innerHTML : '';
        
        runBtn.innerHTML = '<span class="loading"></span> Running...';
        runBtn.disabled = true;
        
        if (runBtnSidebar) {
            runBtnSidebar.innerHTML = '<span class="loading"></span>';
            runBtnSidebar.disabled = true;
        }

        config.simulation_time_days = parseInt(simulationDaysInput.value);

        const finalConfig = {
            equipment: config.equipment,
            products: config.products,
            changeovers: config.changeovers,
            orders: config.orders,
            hours_per_day: config.hours_per_day,
            simulation_time_days: config.simulation_time_days
        };

        const response = await fetch('/run-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(finalConfig)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        resultsContent.textContent = result.output;
        resultsSection.classList.remove('hidden');

        resultsSection.scrollIntoView({ behavior: 'smooth' });

        // Reset buttons
        runBtn.innerHTML = originalText;
        runBtn.disabled = false;
        
        if (runBtnSidebar) {
            runBtnSidebar.innerHTML = originalSidebarText;
            runBtnSidebar.disabled = false;
        }

    } catch (error) {
        console.error('Error running simulation:', error);
        alert('Error running simulation: ' + error.message);
        
        // Reset buttons on error
        runBtn.innerHTML = '<span class="btn-icon">🚀</span> Run Simulation';
        runBtn.disabled = false;
        
        if (runBtnSidebar) {
            runBtnSidebar.innerHTML = '<span class="run-icon">🚀</span><span class="run-text">Run Simulation</span>';
            runBtnSidebar.disabled = false;
        }
    }
}

// Load configuration from localStorage on page load
function loadSavedConfiguration() {
    const saved = localStorage.getItem('plantConfig');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            config = parsed;
            
            // Reinitialize availableIds
            availableIds = {
                'Reactor': new Set(),
                'Dryer': new Set(),
                'Packager': new Set()
            };
            
            simulationDaysInput.value = config.simulation_time_days;

            refreshEquipmentList();
            refreshOrdersList();
            refreshChangeoversList();
            updateSidebarCounts();
        } catch (error) {
            console.error('Error loading saved configuration:', error);
        }
    }
}

// Initialize saved configuration loading
loadSavedConfiguration();

// Run AI Analysis
async function runAIAnalysis() {
    const analyzeBtn = document.getElementById('analyze-ai');
    
    try {
        // Show loading state
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<span class="loading"></span> Analyzing...';
        analyzeBtn.disabled = true;

        const response = await fetch('/analyze-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP error! status: ${response.status}`);
        }

        // Display the AI analysis with markdown-like formatting
        displayAIAnalysis(result.analysis);
        
        aiAnalysisSection.classList.remove('hidden');
        aiAnalysisSection.scrollIntoView({ behavior: 'smooth' });

        // Reset button
        analyzeBtn.innerHTML = originalText;
        analyzeBtn.disabled = false;

    } catch (error) {
        console.error('Error running AI analysis:', error);
        alert('Error running AI analysis: ' + error.message);
        
        // Reset button on error
        analyzeBtn.innerHTML = '<span class="btn-icon">🤖</span> Analyze with AI';
        analyzeBtn.disabled = false;
    }
}

// Display AI Analysis with enhanced formatting
function displayAIAnalysis(analysis) {
    // Process the analysis line by line for better control
    const lines = analysis.split('\n');
    let html = '';
    let inTable = false;
    let inList = false;
    let listType = null;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        
        // Check for table rows (lines with |)
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
            // Check if this is a separator row (|---|---|)
            if (line.includes('---')) {
                continue; // Skip separator rows
            }
            
            if (!inTable) {
                // Close any open list
                if (inList) {
                    html += listType === 'ul' ? '</ul>' : '</ol>';
                    inList = false;
                }
                html += '<div class="table-container"><table class="ai-table">';
                inTable = true;
                // First row is header
                const cells = line.split('|').filter(cell => cell.trim() !== '');
                html += '<thead><tr>';
                cells.forEach(cell => {
                    html += `<th>${formatInlineText(cell.trim())}</th>`;
                });
                html += '</tr></thead><tbody>';
            } else {
                const cells = line.split('|').filter(cell => cell.trim() !== '');
                html += '<tr>';
                cells.forEach(cell => {
                    html += `<td>${formatInlineText(cell.trim())}</td>`;
                });
                html += '</tr>';
            }
            continue;
        } else if (inTable) {
            html += '</tbody></table></div>';
            inTable = false;
        }
        
        // Headers (####, ###, ##, #)
        if (line.startsWith('####')) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += `<h4 class="ai-h4">${formatInlineText(line.replace(/^####\s*/, ''))}</h4>`;
            continue;
        }
        if (line.startsWith('###')) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += `<h3 class="ai-h3">${formatInlineText(line.replace(/^###\s*/, ''))}</h3>`;
            continue;
        }
        if (line.startsWith('##')) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += `<h2 class="ai-h2">${formatInlineText(line.replace(/^##\s*/, ''))}</h2>`;
            continue;
        }
        if (line.startsWith('#')) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += `<h1 class="ai-h1">${formatInlineText(line.replace(/^#\s*/, ''))}</h1>`;
            continue;
        }
        
        // Bullet points
        if (line.trim().match(/^[-*]\s+/)) {
            if (!inList || listType !== 'ul') {
                if (inList) html += '</ol>';
                html += '<ul class="ai-list">';
                inList = true;
                listType = 'ul';
            }
            html += `<li>${formatInlineText(line.trim().replace(/^[-*]\s+/, ''))}</li>`;
            continue;
        }
        
        // Numbered lists
        if (line.trim().match(/^\d+\.\s+/)) {
            if (!inList || listType !== 'ol') {
                if (inList) html += '</ul>';
                html += '<ol class="ai-list">';
                inList = true;
                listType = 'ol';
            }
            html += `<li>${formatInlineText(line.trim().replace(/^\d+\.\s+/, ''))}</li>`;
            continue;
        }
        
        // Close list if we hit a non-list line
        if (inList && line.trim() !== '') {
            html += listType === 'ul' ? '</ul>' : '</ol>';
            inList = false;
        }
        
        // Empty line = paragraph break
        if (line.trim() === '') {
            html += '<div class="spacer"></div>';
            continue;
        }
        
        // Regular paragraph
        html += `<p class="ai-paragraph">${formatInlineText(line)}</p>`;
    }
    
    // Close any remaining open tags
    if (inTable) html += '</tbody></table></div>';
    if (inList) html += listType === 'ul' ? '</ul>' : '</ol>';
    
    aiAnalysisContent.innerHTML = `<div class="ai-analysis-text">${html}</div>`;
}

// Format inline text (bold, italic, code)
function formatInlineText(text) {
    return text
        // Bold text **text** or __text__
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        // Italic text *text* or _text_
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        // Inline code `code`
        .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
        // Colon-separated key-value pairs for emphasis
        .replace(/^([A-Za-z\s]+):\s*/gm, '<strong class="key-label">$1:</strong> ');
}