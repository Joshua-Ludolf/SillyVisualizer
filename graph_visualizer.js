// D3.js Graph Visualizer

class GraphVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.width = 800;
        this.height = 600;
        this.nodeRadius = 20;
        this.zoom = null;
        this.tooltip = null;
        this.minZoom = 0.1;
        this.maxZoom = 5.0;
        this.zoomStep = 1.3;
        this.nodeTypes = {
            'Module': { color: '#2C3E50', description: 'Module/File' },
            'Class': { color: '#3498DB', description: 'Class Definition', types: ['ClassDef', 'ClassDeclaration'] },
            'Function': { color: '#2ECC71', description: 'Function/Method', types: ['FunctionDef', 'MethodDeclaration'] },
            'Name': { color: '#F39C12', description: 'Variable/Identifier' },
            'Attribute': { color: '#9B59B6', description: 'Object Property' },
            'Call': { color: '#16A085', description: 'Function Call' },
            'Control': { color: '#E74C3C', description: 'Control Flow', types: ['If', 'For', 'While'] },
            'default': { color: '#95A5A6', description: 'Other Element' }
        };

        // Create a mapping for quick node type lookups
        this.nodeTypeMapping = {};
        Object.entries(this.nodeTypes).forEach(([key, value]) => {
            if (value.types) {
                value.types.forEach(type => {
                    this.nodeTypeMapping[type] = key;
                });
            } else {
                this.nodeTypeMapping[key] = key;
            }
        });
    }

    initialize() {
        // Create SVG container
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [-this.width / 2, -this.height / 2, this.width, this.height]);

        // Create defs for gradients
        const defs = this.svg.append('defs');

        // Create gradients for each node type
        Object.entries(this.nodeTypes).forEach(([key, value]) => {
            const gradient = defs.append('radialGradient')
                .attr('id', `gradient-${key}`)
                .attr('cx', '50%')
                .attr('cy', '50%')
                .attr('r', '50%')
                .attr('fx', '50%')
                .attr('fy', '50%');

            const baseColor = d3.color(value.color);
            const lighterColor = baseColor.brighter(0.5);
            const darkerColor = baseColor.darker(0.5);

            gradient.append('stop')
                .attr('offset', '0%')
                .attr('stop-color', lighterColor.toString());

            gradient.append('stop')
                .attr('offset', '100%')
                .attr('stop-color', darkerColor.toString());
        });

        // Create tooltip div
        this.tooltip = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'node-tooltip')
            .style('position', 'absolute')
            .style('visibility', 'hidden')
            .style('background-color', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000');

        // Create a group for the graph content
        this.graphGroup = this.svg.append('g')
            .attr('class', 'graph-content');

        // Create arrow marker for directed edges
        this.graphGroup.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Initialize zoom behavior with improved settings
        this.zoom = d3.zoom()
            .scaleExtent([this.minZoom, this.maxZoom])
            .on('zoom', (event) => {
                this.graphGroup.attr('transform', event.transform);
                this.updateZoomInfo(event.transform.k);
            });

        // Apply zoom behavior to SVG
        this.svg.call(this.zoom)
            .call(this.zoom.transform, d3.zoomIdentity);

        // Initialize force simulation with improved settings
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(120).strength(0.5))
            .force('charge', d3.forceManyBody().strength(-400).distanceMax(300))
            .force('center', d3.forceCenter(0, 0))
            .force('collision', d3.forceCollide().radius(this.nodeRadius + 5))
            .on('tick', () => this.tick());

        // DON'T create controls and legend immediately - wait for data
        this.controlsCreated = false;
        this.initialized = true;
    }
    
    hideControls() {
        // Hide all control elements
        d3.select(`#${this.containerId}`).selectAll('.controls-container').style('display', 'none');
        d3.select(`#${this.containerId}`).selectAll('.legend').style('display', 'none');
        d3.select(`#${this.containerId}`).selectAll('.shortcuts-toggle').style('display', 'none');
        d3.select(`#${this.containerId}`).selectAll('.shortcuts-info').style('display', 'none');
    }
    
    showControls() {
        // Show all control elements when visualization is active
        d3.select(`#${this.containerId}`).selectAll('.controls-container').style('display', 'flex');
        d3.select(`#${this.containerId}`).selectAll('.legend').style('display', 'block');
        d3.select(`#${this.containerId}`).selectAll('.shortcuts-toggle').style('display', 'block');
    }

    addZoomControls() {
        const controlsContainer = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'controls-container')
            .style('position', 'absolute')
            .style('bottom', '20px')
            .style('right', '20px')
            .style('display', 'flex')
            .style('flex-direction', 'column')
            .style('gap', '12px')
            .style('z-index', '1000');

        // Zoom controls group
        const zoomControls = controlsContainer
            .append('div')
            .attr('class', 'zoom-controls')
            .style('display', 'flex')
            .style('flex-direction', 'column')
            .style('gap', '8px')
            .style('background', 'rgba(255, 255, 255, 0.9)')
            .style('padding', '8px')
            .style('border-radius', '8px')
            .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)');

        // Zoom level display
        this.zoomDisplay = zoomControls.append('div')
            .attr('class', 'zoom-display')
            .style('text-align', 'center')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .style('color', '#333')
            .style('margin-bottom', '4px')
            .text('100%');

        // Zoom in button
        zoomControls.append('button')
            .attr('class', 'zoom-button')
            .style('padding', '8px 12px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '16px')
            .style('font-weight', 'bold')
            .text('⊕')
            .on('click', () => this.zoomIn())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        // Zoom out button
        zoomControls.append('button')
            .attr('class', 'zoom-button')
            .style('padding', '8px 12px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '16px')
            .style('font-weight', 'bold')
            .text('⊖')
            .on('click', () => this.zoomOut())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        // Reset/Recenter button
        zoomControls.append('button')
            .attr('class', 'zoom-button')
            .style('padding', '8px 12px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '14px')
            .style('font-weight', 'bold')
            .text('⌂')
            .attr('title', 'Recenter and fit to view')
            .on('click', () => this.recenterAndFit())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        // Fit to view button
        zoomControls.append('button')
            .attr('class', 'zoom-button')
            .style('padding', '8px 12px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '14px')
            .style('font-weight', 'bold')
            .text('⬚')
            .attr('title', 'Fit all nodes to view')
            .on('click', () => this.fitToView())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        // View controls group
        const viewControls = controlsContainer
            .append('div')
            .attr('class', 'view-controls')
            .style('display', 'flex')
            .style('flex-direction', 'column')
            .style('gap', '8px')
            .style('background', 'rgba(255, 255, 255, 0.9)')
            .style('padding', '8px')
            .style('border-radius', '8px')
            .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)');

        // Restart simulation button
        viewControls.append('button')
            .attr('class', 'control-button')
            .style('padding', '6px 10px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '12px')
            .text('🔄 Restart')
            .attr('title', 'Restart force simulation')
            .on('click', () => this.restartSimulation())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        // Pause/Resume simulation button
        this.pauseButton = viewControls.append('button')
            .attr('class', 'control-button')
            .style('padding', '6px 10px')
            .style('border', '1px solid #ddd')
            .style('background', '#fff')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('font-size', '12px')
            .text('⏸️ Pause')
            .attr('title', 'Pause/Resume force simulation')
            .on('click', () => this.toggleSimulation())
            .on('mouseover', function() { 
                d3.select(this).style('background', '#f0f0f0'); 
            })
            .on('mouseout', function() { 
                d3.select(this).style('background', '#fff'); 
            });

        this.simulationRunning = true;
    }

    addKeyboardControls() {
        // Add keyboard event listeners
        d3.select('body').on('keydown', (event) => {
            // Only handle keyboard shortcuts when the container is focused or hovered
            const container = document.getElementById(this.containerId);
            if (!container || (!container.matches(':hover') && document.activeElement !== container)) {
                return;
            }

            switch(event.key) {
                case '+':
                case '=':
                    event.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                case '_':
                    event.preventDefault();
                    this.zoomOut();
                    break;
                case '0':
                    event.preventDefault();
                    this.recenterAndFit();
                    break;
                case 'f':
                case 'F':
                    event.preventDefault();
                    this.fitToView();
                    break;
                case 'r':
                case 'R':
                    event.preventDefault();
                    this.restartSimulation();
                    break;
                case ' ':
                    event.preventDefault();
                    this.toggleSimulation();
                    break;
            }
        });

        // Make container focusable for keyboard events
        d3.select(`#${this.containerId}`)
            .attr('tabindex', '0')
            .style('outline', 'none');
    }

    zoomIn() {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleBy, this.zoomStep);
    }

    zoomOut() {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleBy, 1 / this.zoomStep);
    }

    recenterAndFit() {
        this.svg.transition()
            .duration(500)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    fitToView() {
        if (!this.nodes || this.nodes.length === 0) return;

        // Calculate bounds of all nodes
        const bounds = this.calculateNodeBounds();
        if (!bounds) return;

        const dx = bounds.x[1] - bounds.x[0];
        const dy = bounds.y[1] - bounds.y[0];
        const x = (bounds.x[0] + bounds.x[1]) / 2;
        const y = (bounds.y[0] + bounds.y[1]) / 2;

        const scale = Math.min(
            0.9 / Math.max(dx / this.width, dy / this.height),
            this.maxZoom
        );

        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, 
                d3.zoomIdentity.translate(this.width / 2, this.height / 2).scale(scale).translate(-x, -y)
            );
    }

    calculateNodeBounds() {
        if (!this.nodes || this.nodes.length === 0) return null;

        const xs = this.nodes.map(d => d.x).filter(x => x !== undefined);
        const ys = this.nodes.map(d => d.y).filter(y => y !== undefined);

        if (xs.length === 0 || ys.length === 0) return null;

        return {
            x: [Math.min(...xs) - 50, Math.max(...xs) + 50],
            y: [Math.min(...ys) - 50, Math.max(...ys) + 50]
        };
    }

    restartSimulation() {
        if (this.simulation) {
            this.simulation.alpha(1).restart();
        }
    }

    toggleSimulation() {
        if (this.simulationRunning) {
            this.simulation.stop();
            this.pauseButton.text('▶️ Resume');
            this.simulationRunning = false;
        } else {
            this.simulation.restart();
            this.pauseButton.text('⏸️ Pause');
            this.simulationRunning = true;
        }
    }

    updateZoomInfo(scale) {
        if (this.zoomDisplay) {
            const percentage = Math.round(scale * 100);
            this.zoomDisplay.text(`${percentage}%`);
        }
    }

    // Clear the visualization and hide all controls
    clear() {
        // Clear graph data
        this.nodes = [];
        this.links = [];
        
        // Clear SVG content (except defs and basic structure)
        if (this.graphGroup) {
            this.graphGroup.selectAll('.link').remove();
            this.graphGroup.selectAll('.node').remove();
        }
        
        // Hide and remove controls if they exist
        if (this.controlsCreated) {
            d3.select(`#${this.containerId} .controls-container`).remove();
            d3.select(`#${this.containerId} .legend`).remove();
            d3.select(`#${this.containerId} .shortcuts-info`).remove();
            d3.select(`#${this.containerId} .shortcuts-toggle`).remove();
            this.controlsCreated = false;
        }
        
        // Hide tooltip
        if (this.tooltip) {
            this.tooltip.style('visibility', 'hidden');
        }
        
        // Reset zoom
        if (this.svg && this.zoom) {
            this.svg.call(this.zoom.transform, d3.zoomIdentity);
        }
        
        // Stop simulation
        if (this.simulation) {
            this.simulation.stop();
        }
    }

    createLegend() {
        // Create legend container
        const legend = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'legend')
            .style('position', 'absolute')
            .style('top', '20px')
            .style('left', '20px')
            .style('background', 'rgba(255, 255, 255, 0.95)')
            .style('padding', '12px')
            .style('border-radius', '8px')
            .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
            .style('max-width', '200px')
            .style('z-index', '1000');

        // Add collapsible title
        const header = legend.append('div')
            .style('display', 'flex')
            .style('justify-content', 'space-between')
            .style('align-items', 'center')
            .style('margin-bottom', '8px')
            .style('cursor', 'pointer');

        header.append('div')
            .style('font-weight', 'bold')
            .style('font-size', '14px')
            .text('Node Types');

        this.legendToggle = header.append('div')
            .style('font-size', '12px')
            .style('color', '#666')
            .text('−');

        this.legendContent = legend.append('div')
            .attr('class', 'legend-content');

        // Add legend items with interactive features
        const items = this.legendContent.selectAll('.legend-item')
            .data(Object.entries(this.nodeTypes).filter(d => d[0] !== 'default'))
            .enter()
            .append('div')
            .attr('class', 'legend-item')
            .style('display', 'flex')
            .style('align-items', 'center')
            .style('margin', '6px 0')
            .style('padding', '4px')
            .style('border-radius', '4px')
            .style('cursor', 'pointer')
            .style('transition', 'background-color 0.2s')
            .on('mouseover', function(event, d) {
                d3.select(this).style('background-color', '#f0f0f0');
                // Highlight corresponding nodes
                d3.selectAll(`.node-${d[0]}`)
                    .select('circle')
                    .style('stroke', '#ffd700')
                    .style('stroke-width', '3px');
            })
            .on('mouseout', function(event, d) {
                d3.select(this).style('background-color', 'transparent');
                // Remove highlight from nodes
                d3.selectAll(`.node-${d[0]}`)
                    .select('circle')
                    .style('stroke', '#fff')
                    .style('stroke-width', '1.5px');
            });

        // Add color circle
        items.append('div')
            .style('width', '14px')
            .style('height', '14px')
            .style('border-radius', '50%')
            .style('margin-right', '10px')
            .style('background', d => d[1].color)
            .style('border', '1px solid #ddd')
            .style('flex-shrink', '0');

        // Add description
        items.append('div')
            .style('font-size', '12px')
            .style('flex-grow', '1')
            .text(d => d[1].description);

        // Add toggle functionality
        let legendExpanded = true;
        header.on('click', () => {
            legendExpanded = !legendExpanded;
            this.legendContent.style('display', legendExpanded ? 'block' : 'none');
            this.legendToggle.text(legendExpanded ? '−' : '+');
        });

        // Add keyboard shortcuts info
        this.addKeyboardShortcutsInfo();
    }

    addKeyboardShortcutsInfo() {
        const shortcutsInfo = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'shortcuts-info')
            .style('position', 'absolute')
            .style('top', '20px')
            .style('right', '240px')
            .style('background', 'rgba(255, 255, 255, 0.95)')
            .style('padding', '8px')
            .style('border-radius', '6px')
            .style('box-shadow', '0 2px 6px rgba(0,0,0,0.1)')
            .style('font-size', '11px')
            .style('z-index', '1000')
            .style('display', 'none');

        shortcutsInfo.append('div')
            .style('font-weight', 'bold')
            .style('margin-bottom', '4px')
            .text('Keyboard Shortcuts:');

        const shortcuts = [
            '+ : Zoom In',
            '− : Zoom Out', 
            '0 : Recenter',
            'F : Fit to View',
            'R : Restart Simulation',
            'Space : Pause/Resume'
        ];

        shortcuts.forEach(shortcut => {
            shortcutsInfo.append('div')
                .style('margin', '2px 0')
                .text(shortcut);
        });

        // Add toggle for shortcuts info
        const shortcutsToggle = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'shortcuts-toggle')
            .style('position', 'absolute')
            .style('top', '20px')
            .style('right', '200px')
            .style('background', 'rgba(255, 255, 255, 0.9)')
            .style('padding', '6px 8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('cursor', 'pointer')
            .style('border', '1px solid #ddd')
            .style('z-index', '1000')
            .text('⌨️')
            .attr('title', 'Show keyboard shortcuts');

        let shortcutsVisible = false;
        shortcutsToggle.on('click', () => {
            shortcutsVisible = !shortcutsVisible;
            shortcutsInfo.style('display', shortcutsVisible ? 'block' : 'none');
        });
    }

    // Update visualization with new data
    update(data) {
        console.log('GraphVisualizer.update called with:', data);
        console.log('Nodes count:', data.nodes ? data.nodes.length : 'no nodes');
        console.log('Links count:', data.links ? data.links.length : 'no links');
        
        this.nodes = data.nodes;
        this.links = data.links;

        // Dynamically adjust node radius based on number of nodes for better visibility
        const nodeCount = this.nodes.length;
        if (nodeCount > 500) {
            this.nodeRadius = 8;  // Smaller for very large graphs
        } else if (nodeCount > 200) {
            this.nodeRadius = 12; // Medium for large graphs
        } else if (nodeCount > 50) {
            this.nodeRadius = 16; // Default for medium graphs
        } else {
            this.nodeRadius = 20; // Larger for small graphs
        }
        
        console.log(`Adjusted node radius to ${this.nodeRadius} for ${nodeCount} nodes`);

        // Create controls and legend only when we have actual data to visualize
        if (!this.controlsCreated && this.nodes.length > 0) {
            this.addZoomControls();
            this.addKeyboardControls();
            this.createLegend();
            this.controlsCreated = true;
            // Show controls now that they're created
            this.showControls();
        }

        // Update links with enhanced styling
        this.linkElements = this.graphGroup.selectAll('.link')
            .data(this.links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke', d => {
                // Color links based on relationship type
                if (d.type === 'inheritance') return '#e74c3c';
                if (d.type === 'composition') return '#3498db';
                if (d.type === 'dependency') return '#f39c12';
                return '#999';
            })
            .attr('stroke-width', d => {
                // Vary width based on relationship importance
                if (d.weight && d.weight > 1) return Math.min(d.weight, 4);
                if (d.type === 'inheritance') return 2.5;
                if (d.type === 'composition') return 2;
                return 1.5;
            })
            .attr('stroke-opacity', 0.8)
            .attr('marker-end', 'url(#arrowhead)')
            .style('stroke-dasharray', d => {
                // Use dashed lines for certain relationship types
                if (d.type === 'dependency') return '5,5';
                return null;
            });

        // Update nodes
        this.nodeElements = this.graphGroup.selectAll('.node')
            .data(this.nodes)
            .join('g')
            .attr('class', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return `node node-${mappedType}`;
            })
            .call(this.drag())
            .on('mouseover', (event, d) => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                const nodeType = this.nodeTypes[mappedType];
                
                // Get full path/name
                const fullName = d.value || d.label || '';
                
                // Count connections
                const connections = this.links.filter(link => 
                    link.source === d || link.target === d || 
                    link.source.id === d.id || link.target.id === d.id
                ).length;
                
                // Create enhanced tooltip content
                const details = [
                    `Name: ${fullName || 'Unnamed'}`,
                    `Type: ${nodeType.description}`,
                    `Connections: ${connections}`,
                    d.lineno ? `Line: ${d.lineno}` : null,
                    d.details ? `Details: ${d.details}` : null
                ].filter(Boolean).join('\n');

                // Position tooltip relative to the container
                const containerRect = document.getElementById(this.containerId).getBoundingClientRect();
                const xOffset = event.clientX - containerRect.left + 15;
                const yOffset = event.clientY - containerRect.top - 10;

                this.tooltip
                    .style('visibility', 'visible')
                    .style('left', xOffset + 'px')
                    .style('top', yOffset + 'px')
                    .style('white-space', 'pre-line')
                    .style('max-width', '250px')
                    .html(details.replace(/\n/g, '<br/>'));

                // Highlight the node and its connections
                d3.select(event.currentTarget).select('circle')
                    .style('stroke', '#ffd700')
                    .style('stroke-width', '4px')
                    .style('filter', 'drop-shadow(0 0 8px rgba(255,215,0,0.6))');

                // Highlight connected links
                this.linkElements
                    .style('stroke-opacity', link => {
                        const isConnected = link.source === d || link.target === d || 
                                          link.source.id === d.id || link.target.id === d.id;
                        return isConnected ? 1 : 0.2;
                    })
                    .style('stroke-width', link => {
                        const isConnected = link.source === d || link.target === d || 
                                          link.source.id === d.id || link.target.id === d.id;
                        return isConnected ? 3 : 1;
                    });

                // Highlight connected nodes
                this.nodeElements.selectAll('circle')
                    .style('opacity', node => {
                        if (node === d) return 1;
                        const isConnected = this.links.some(link => 
                            (link.source === d && link.target === node) ||
                            (link.target === d && link.source === node) ||
                            (link.source.id === d.id && link.target.id === node.id) ||
                            (link.target.id === d.id && link.source.id === node.id)
                        );
                        return isConnected ? 1 : 0.3;
                    });
            })
            .on('mousemove', (event) => {
                // Update tooltip position relative to the container
                const containerRect = document.getElementById(this.containerId).getBoundingClientRect();
                const xOffset = event.clientX - containerRect.left + 10;
                const yOffset = event.clientY - containerRect.top - 10;

                this.tooltip
                    .style('left', xOffset + 'px')
                    .style('top', yOffset + 'px');
            })
            .on('mouseout', (event) => {
                this.tooltip.style('visibility', 'hidden');
                
                // Remove all highlights
                d3.select(event.currentTarget).select('circle')
                    .style('stroke', '#fff')
                    .style('stroke-width', '2px')
                    .style('filter', 'drop-shadow(2px 2px 4px rgba(0,0,0,0.3))');

                // Reset link styles
                this.linkElements
                    .style('stroke-opacity', 0.8)
                    .style('stroke-width', d => {
                        if (d.weight && d.weight > 1) return Math.min(d.weight, 4);
                        if (d.type === 'inheritance') return 2.5;
                        if (d.type === 'composition') return 2;
                        return 1.5;
                    });

                // Reset node opacity
                this.nodeElements.selectAll('circle')
                    .style('opacity', 1);
            });

        // Clear existing circles and labels
        this.nodeElements.selectAll('*').remove();

        // Add circles to nodes with enhanced styling
        this.nodeElements.append('circle')
            .attr('r', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                // Vary radius based on node type and importance
                if (mappedType === 'Class') return this.nodeRadius * 1.2;
                if (mappedType === 'Function') return this.nodeRadius * 1.1;
                if (mappedType === 'Module') return this.nodeRadius * 1.3;
                return this.nodeRadius;
            })
            .attr('fill', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return `url(#gradient-${mappedType})`;
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(2px 2px 4px rgba(0,0,0,0.3))')
            .style('transition', 'all 0.3s ease');

        // Add labels to nodes with improved positioning
        this.nodeElements.append('text')
            .text(d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                const name = d.value || d.label || '';
                
                // Show text for more node types with truncation
                if (mappedType === 'Class' || mappedType === 'Function' || mappedType === 'Module') {
                    const displayName = name.split('/').pop() || name;
                    return displayName.length > 12 ? displayName.substring(0, 10) + '...' : displayName;
                }
                return '';
            })
            .attr('text-anchor', 'middle')
            .attr('dy', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                // Position text below larger nodes
                if (mappedType === 'Module') return this.nodeRadius * 1.8;
                if (mappedType === 'Class') return this.nodeRadius * 1.7;
                if (mappedType === 'Function') return this.nodeRadius * 1.6;
                return '.35em';
            })
            .attr('fill', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                // Use contrasting colors
                if (mappedType === 'Module' || mappedType === 'Class' || mappedType === 'Function') {
                    return '#333';
                }
                return '#000';
            })
            .style('font-size', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                if (mappedType === 'Module') return '11px';
                if (mappedType === 'Class') return '10px';
                if (mappedType === 'Function') return '9px';
                return '8px';
            })
            .style('font-weight', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                if (mappedType === 'Module' || mappedType === 'Class') return 'bold';
                return 'normal';
            })
            .style('pointer-events', 'none')
            .style('text-shadow', '1px 1px 2px rgba(255,255,255,0.8)');

        // Add node count badge for classes/modules
        this.nodeElements
            .filter(d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Class' || mappedType === 'Module';
            })
            .append('circle')
            .attr('r', 8)
            .attr('cx', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Module' ? this.nodeRadius * 1.0 : this.nodeRadius * 0.8;
            })
            .attr('cy', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Module' ? -this.nodeRadius * 1.0 : -this.nodeRadius * 0.8;
            })
            .attr('fill', '#ff6b6b')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);

        // Add count text for badges
        this.nodeElements
            .filter(d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Class' || mappedType === 'Module';
            })
            .append('text')
            .attr('x', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Module' ? this.nodeRadius * 1.0 : this.nodeRadius * 0.8;
            })
            .attr('y', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return mappedType === 'Module' ? -this.nodeRadius * 1.0 + 3 : -this.nodeRadius * 0.8 + 3;
            })
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .style('font-size', '8px')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text(d => {
                // Count related nodes (simplified)
                return this.links.filter(link => 
                    link.source === d || link.target === d || 
                    link.source.id === d.id || link.target.id === d.id
                ).length;
            });

        // Update simulation with dynamic parameters based on node count
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        
        // Adjust simulation forces based on graph size and node radius
        const linkDistance = this.nodeRadius * 4; // Scale link distance with node size
        const chargeStrength = nodeCount > 200 ? -200 : -400; // Weaker charge for large graphs
        const collisionRadius = this.nodeRadius + 3; // Collision based on actual node radius
        
        this.simulation
            .force('link', d3.forceLink().id(d => d.id).distance(linkDistance).strength(0.5))
            .force('charge', d3.forceManyBody().strength(chargeStrength).distanceMax(300))
            .force('collision', d3.forceCollide().radius(collisionRadius));
            
        console.log(`Updated simulation: linkDistance=${linkDistance}, chargeStrength=${chargeStrength}, collisionRadius=${collisionRadius}`);
        
        this.simulation.alpha(1).restart();

        // Auto-fit to view after a short delay to let simulation settle
        setTimeout(() => {
            this.fitToView();
        }, 1000);
    }

    // Handle simulation tick
    tick() {
        if (this.linkElements) {
            this.linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }

        if (this.nodeElements) {
            this.nodeElements.attr('transform', d => `translate(${d.x},${d.y})`);
        }
    }

    // Create drag behavior that works with zoom
    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
}

// Initialize visualizer when document is ready
$(document).ready(() => {
    window.graphVisualizer = new GraphVisualizer('result');
    window.graphVisualizer.initialize();
});
