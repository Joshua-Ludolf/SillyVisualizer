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

        // Initialize zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4]) // Allow zooming from 0.1x to 4x
            .on('zoom', (event) => {
                this.graphGroup.attr('transform', event.transform);
            });

        // Apply zoom behavior to SVG
        this.svg.call(this.zoom)
            .call(this.zoom.transform, d3.zoomIdentity);

        // Add zoom controls
        this.addZoomControls();

        // Initialize force simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('x', d3.forceX())
            .force('y', d3.forceY())
            .on('tick', () => this.tick());

        // Create legend
        this.createLegend();
    }

    addZoomControls() {
        const controls = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'zoom-controls')
            .style('position', 'absolute')
            .style('bottom', '20px')
            .style('right', '20px')
            .style('display', 'flex')
            .style('flex-direction', 'column')
            .style('gap', '8px');

        // Zoom in button
        controls.append('button')
            .attr('class', 'zoom-button')
            .text('+')
            .on('click', () => {
                this.svg.transition()
                    .duration(300)
                    .call(this.zoom.scaleBy, 1.5);
            });

        // Zoom out button
        controls.append('button')
            .attr('class', 'zoom-button')
            .text('−')
            .on('click', () => {
                this.svg.transition()
                    .duration(300)
                    .call(this.zoom.scaleBy, 0.75);
            });

        // Reset zoom button
        controls.append('button')
            .attr('class', 'zoom-button')
            .text('⟲')
            .on('click', () => {
                this.svg.transition()
                    .duration(300)
                    .call(this.zoom.transform, d3.zoomIdentity);
            });
    }

    createLegend() {
        // Create legend container
        const legend = d3.select(`#${this.containerId}`)
            .append('div')
            .attr('class', 'legend')
            .style('position', 'absolute')
            .style('top', '20px')
            .style('right', '20px')
            .style('background', 'white')
            .style('padding', '10px')
            .style('border-radius', '8px')
            .style('box-shadow', '0 2px 4px rgba(0,0,0,0.1)');

        // Add title
        legend.append('div')
            .style('font-weight', 'bold')
            .style('margin-bottom', '8px')
            .text('Node Types');

        // Add legend items (only for main types, not the mapping)
        const items = legend.selectAll('.legend-item')
            .data(Object.entries(this.nodeTypes))
            .enter()
            .append('div')
            .attr('class', 'legend-item')
            .style('display', 'flex')
            .style('align-items', 'center')
            .style('margin', '4px 0');

        // Add color circle
        items.append('div')
            .style('width', '12px')
            .style('height', '12px')
            .style('border-radius', '50%')
            .style('margin-right', '8px')
            .style('background', d => d[1].color);

        // Add description
        items.append('div')
            .style('font-size', '12px')
            .text(d => d[1].description);
    }

    // Update visualization with new data
    update(data) {
        this.nodes = data.nodes;
        this.links = data.links;

        // Update links
        this.linkElements = this.graphGroup.selectAll('.link')
            .data(this.links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-width', 1)
            .attr('marker-end', 'url(#arrowhead)');

        // Update nodes
        this.nodeElements = this.graphGroup.selectAll('.node')
            .data(this.nodes)
            .join('g')
            .attr('class', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return `node node-${mappedType}`;
            })
            .call(this.drag());

        // Clear existing circles and labels
        this.nodeElements.selectAll('*').remove();

        // Add circles to nodes
        this.nodeElements.append('circle')
            .attr('r', this.nodeRadius)
            .attr('fill', d => {
                const mappedType = this.nodeTypeMapping[d.type] || 'default';
                return this.nodeTypes[mappedType]?.color || this.nodeTypes.default.color;
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);

        // Add labels to nodes
        this.nodeElements.append('text')
            .text(d => d.value || d.label)
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('fill', '#fff')
            .style('font-size', '10px')
            .style('pointer-events', 'none')
            .each(function(d) {
                // Wrap text if too long
                let text = d3.select(this);
                let words = (d.value || d.label).split(/\s+/);
                if (words.length > 2) {
                    text.text(words.slice(0, 2).join(' ') + '...');
                }
            });

        // Update simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(1).restart();
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
});
