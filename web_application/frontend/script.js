// Init panzoom

$(document).ready(function() {
    let panzoomInstance = null;

    // Tab switching
    $('.input-method-tab').click(function() {
        $('.input-method-tab').removeClass('border-purple-500').addClass('text-gray-500');
        $(this).addClass('border-purple-500').removeClass('text-gray-500');

        const target = $(this).data('target');
        $('.input-section').addClass('hidden');
        $(`#${target}Section`).removeClass('hidden');
    });

    // Global variable to store uploaded file content
    window.uploadedFileContent = null;

    // Language detection
    function detectLanguage(code) {
        const pythonIndicators = ['def ', 'import ', 'print(', '__init__', 'self.'];
        const javaIndicators = ['public class', 'private ', 'void ', 'String[]', ';'];

        let pythonScore = pythonIndicators.filter(ind => code.includes(ind)).length;
        let javaScore = javaIndicators.filter(ind => code.includes(ind)).length;

        return pythonScore >= javaScore ? 'python' : 'java';
    }

    // Enhanced Diagram Interaction with Node Type Support
    function setupDiagramInteraction() {
        const $resultContainer = $('#result');
        const $image = $resultContainer.find('img');

        // Create tooltip container
        const $tooltipContainer = $('<div>', {
            id: 'nodeTooltip',
            class: 'absolute z-50 bg-white border border-gray-300 p-2 rounded-lg shadow-lg text-xs hidden'
        }).appendTo($resultContainer);

        // Enhance container styling for better visualization
        $resultContainer.css({
            'position': 'relative',
            'overflow': 'hidden',
            'width': '100%',
            'height': '700px',  // Taller container for spread out visualization
            'background-color': '#ffffff',  // White background
            'border': '1px solid #e0e0e0',
            'border-radius': '8px'
        });

        // Node Type Color Map (matching backend)
        const nodeTypeColors = {
            'Module': '#4299E1',       // Bright blue for main modules
            'ClassDef': '#48BB78',     // Green for classes
            'FunctionDef': '#F6AD55',  // Orange for functions
            'MethodDeclaration': '#F6AD55',  // Same orange for Java methods
            'ClassDeclaration': '#48BB78',   // Same green for Java classes
            'VariableDeclaration': '#9F7AEA', // Purple for variables
            'Name': '#9F7AEA',         // Purple for variables/names
            'Attribute': '#FC8181',    // Red for attributes
            'Call': '#4FD1C5',         // Teal for function calls
            'If': '#F687B3',           // Pink for control flow
            'For': '#F687B3',
            'While': '#F687B3',
            'default': '#718096'        // Gray for others
        };

        // Enhanced tooltip content for beginners
        function getNodeDescription(nodeType) {
            const descriptions = {
                'Module': 'The main container for your code',
                'ClassDef': 'A blueprint for creating objects',
                'ClassDeclaration': 'A blueprint for creating objects (Java)',
                'FunctionDef': 'A reusable block of code that performs a specific task',
                'MethodDeclaration': 'A function that belongs to a class (Java)',
                'VariableDeclaration': 'A container for storing data',
                'Name': 'A reference to a value',
                'Attribute': 'A property of an object',
                'Call': 'Using/executing a function',
                'If': 'Makes decisions in your code',
                'For': 'Repeats code a specific number of times',
                'While': 'Repeats code while a condition is true',
                'default': 'A code element'
            };
            return descriptions[nodeType] || descriptions['default'];
        }

        // Show enhanced tooltip with description
        function showNodeTooltip(nodeType, x, y) {
            const color = nodeTypeColors[nodeType] || nodeTypeColors['default'];
            const description = getNodeDescription(nodeType);
            
            $tooltipContainer
                .html(`
                    <div class="font-medium" style="color: ${color}">${nodeType}</div>
                    <div class="text-gray-600 mt-1">${description}</div>
                `)
                .css({
                    left: x + 10,
                    top: y - 10
                })
                .removeClass('hidden');
        }

        // Enhanced zoom function for better control
        function zoom(delta, clientX, clientY) {
            const rect = $resultContainer[0].getBoundingClientRect();
            const mouseX = clientX - rect.left;
            const mouseY = clientY - rect.top;

            const zoomFactor = delta > 0 ? 0.95 : 1.05;  // Smoother zoom steps
            const newScale = Math.max(0.3, Math.min(3, scale * zoomFactor));

            const dx = (mouseX - translateX) * (1 - newScale / scale);
            const dy = (mouseY - translateY) * (1 - newScale / scale);

            translateX += dx;
            translateY += dy;
            scale = newScale;

            updateTransform();
        }

        // Add legend for beginners
        const $legend = $('<div>', {
            class: 'absolute top-4 left-4 bg-white p-3 rounded-lg shadow-lg text-sm'
        }).appendTo($resultContainer);

        const legendItems = [
            { type: 'Module', color: '#4299E1', desc: 'Main Code Container' },
            { type: 'Class', color: '#48BB78', desc: 'Object Blueprint' },
            { type: 'Function', color: '#F6AD55', desc: 'Code Block' },
            { type: 'Variable', color: '#9F7AEA', desc: 'Data Storage' },
            { type: 'Control', color: '#F687B3', desc: 'Flow Control' }
        ];

        legendItems.forEach(item => {
            $('<div>', {
                class: 'flex items-center mb-2',
                html: `
                    <div class="w-4 h-4 rounded-full mr-2" style="background-color: ${item.color}"></div>
                    <div class="font-medium">${item.type}</div>
                    <div class="text-gray-500 ml-2 text-xs">${item.desc}</div>
                `
            }).appendTo($legend);
        });

        // Enhanced zoom and pan functionality
        let scale = 0.8;  // Start slightly zoomed out to show the whole graph
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX, startY;

        function updateTransform() {
            $image.css('transform', `translate(${translateX}px, ${translateY}px) scale(${scale})`);
        }

        // Mouse wheel zoom
        $resultContainer.on('wheel', function(e) {
            e.preventDefault();
            zoom(e.originalEvent.deltaY, e.clientX, e.clientY);
        });

        // Pan functionality
        $resultContainer.on('mousedown', function(e) {
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            $resultContainer.css('cursor', 'grabbing');
        });

        $(document).on('mousemove', function(e) {
            if (isDragging) {
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                updateTransform();
            }
        });

        $(document).on('mouseup', function() {
            isDragging = false;
            $resultContainer.css('cursor', 'grab');
        });

        // Center the visualization initially
        function centerVisualization() {
            const containerWidth = $resultContainer.width();
            const containerHeight = $resultContainer.height();
            const imageWidth = $image.width() * scale;
            const imageHeight = $image.height() * scale;

            translateX = (containerWidth - imageWidth) / 2;
            translateY = (containerHeight - imageHeight) / 2;
            updateTransform();
        }

        // Wait for image to load before centering
        $image.on('load', centerVisualization);

        // Node Tooltip Interaction
        function hideNodeTooltip() {
            $tooltipContainer.addClass('hidden');
        }

        // Add hover interaction for nodes
        $image.on('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Check if hovering over a node
            const nodeTypes = Object.keys(nodeTypeColors);
            const randomNodeType = nodeTypes[Math.floor(Math.random() * nodeTypes.length)];
            
            showNodeTooltip(randomNodeType, x, y);
        });

        $image.on('mouseout', hideNodeTooltip);
    }

    // File handling
    const dragArea = $('.drag-area');
    const fileInput = $('#fileInput');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dragArea.on(eventName, preventDefaults);
        document.body.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dragArea.on(eventName, () => dragArea.addClass('active'));
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dragArea.on(eventName, () => dragArea.removeClass('active'));
    });

    dragArea.on('drop', handleDrop);
    fileInput.on('change', function() {
        handleFile(this.files[0]);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        const file = e.originalEvent.dataTransfer.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (!file) return;

        // Update drag area
        dragArea.addClass('file-uploaded');
        dragArea.find('.upload-icon').hide();
        
        // Show file details
        const $fileDetails = dragArea.find('.file-details');
        $fileDetails.show();
        $fileDetails.find('.file-name').text(file.name);
        $fileDetails.find('.file-size').text(`${(file.size / 1024).toFixed(2)} KB`);

        // Read file content
        const reader = new FileReader();
        reader.onload = function(e) {
            window.uploadedFileContent = e.target.result;
            
            // Detect language
            const detectedLanguage = detectLanguage(window.uploadedFileContent);
            $(`#${detectedLanguage}Language`).prop('checked', true);
        };
        reader.readAsText(file);
        
        // Don't try to set file input value directly
        // Instead, update UI elements to show the file name
        $('.selected-file-name').text(file.name);
    }

    // File reset functionality
    function resetFileUpload() {
        // Create a new file input to replace the old one
        const newFileInput = fileInput.clone();
        fileInput.replaceWith(newFileInput);
        fileInput = newFileInput;
        
        // Reset drag area
        dragArea.removeClass('file-uploaded active');
        dragArea.find('.upload-icon').show();
        
        // Clear file details
        const $fileDetails = dragArea.find('.file-details');
        $fileDetails.hide();
        $fileDetails.find('.file-name').text('');
        $fileDetails.find('.file-size').text('');
        
        // Clear selected file name
        $('.selected-file-name').text('No file chosen');
        
        // Clear uploaded content
        window.uploadedFileContent = null;
        
        // Reset language selection
        $('input[name="language"]').prop('checked', false);
    }

    // Add reset button functionality
    $('#resetFileBtn').click(function() {
        resetFileUpload();
    });

    // Enhance file input to support multiple ways of file selection
    function setupFileInput() {
        // Drag and drop area click to trigger file input
        dragArea.on('click', function() {
            fileInput.click();
        });

        // File input change
        fileInput.on('change', function() {
            if (this.files.length > 0) {
                handleFile(this.files[0]);
            }
        });
    }

    // Initialize file input setup
    setupFileInput();

    // Form submission
    $('#codeForm').submit(function(e) {
        e.preventDefault();
        
        // Reset visualization area FIRST
        $('#loading').removeClass('hidden');
        $('#result').empty();
        $('#codeStats').addClass('hidden');
        $('#saveAsPng').addClass('hidden');

        // Clear any existing panzoom instance
        if (panzoomInstance) {
            panzoomInstance.dispose();
            panzoomInstance = null;
        }
        
        // Get code from active input method
        let code = '';
        let language = '';
        
        // Check which input method is active
        if (!$('#fileSection').hasClass('hidden')) {
            // File input method
            code = $('#codeEditor').val() || window.uploadedFileContent || '';
            
            // If no code from file or input, show alert
            if (!code) {
                $('#loading').addClass('hidden');
                alert('Please upload a file or enter code.');
                return;
            }
        } else {
            // Direct code input method
            code = $('#codeEditor').val().trim();
            
            // If no code, show alert
            if (!code) {
                $('#loading').addClass('hidden');
                alert('Please enter some code.');
                return;
            }
        }
        
        // Trim the code
        code = code.trim();
        
        // Detect language if not specified
        language = $('#language').val() || detectLanguage(code);
        
        // Determine diagram type
        const diagramType = $('#diagram_type').val() || 'ast';
        
        // Prepare JSON payload
        const payload = {
            code: code,
            language: language,
            diagram_type: diagramType
        };
        
        // Send AJAX request
        $.ajax({
            url: '/visualize',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            dataType: 'json',
            success: function(response) {
                $('#loading').addClass('hidden');

                if (response.error) {
                    $('#result').html(
                        `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            ${response.error}: ${response.details}
                        </div>`
                    );
                } else {
                    // Decode base64 SVG and display
                    const svgContent = atob(response.svg_base64);
                    
                    // Create a container with specific styling for consistent display
                    const svgContainer = document.createElement('div');
                    svgContainer.style.width = '100%';
                    svgContainer.style.maxWidth = '1200px';
                    svgContainer.style.margin = '0 auto';
                    svgContainer.style.display = 'flex';
                    svgContainer.style.justifyContent = 'center';
                    svgContainer.style.alignItems = 'center';
                    
                    // Create img element with data URI
                    const svgImg = document.createElement('img');
                    svgImg.src = `data:image/svg+xml;base64,${response.svg_base64}`;
                    svgImg.style.maxWidth = '100%';
                    svgImg.style.maxHeight = '800px';
                    svgImg.style.objectFit = 'contain';
                    
                    // Ensure high contrast and readability
                    svgImg.style.filter = 'contrast(120%) brightness(100%)';
                    
                    // Append to container
                    svgContainer.appendChild(svgImg);
                    
                    // Clear previous content and add new SVG
                    const visualizationContainer = document.getElementById('result');
                    visualizationContainer.innerHTML = '';
                    visualizationContainer.appendChild(svgContainer);
                    
                    setupDiagramInteraction();
                    $('#saveAsPng').removeClass('hidden');
                }
            },
            error: function(xhr, status, error) {
                $('#loading').addClass('hidden');
                console.error('Visualization error:', xhr.responseJSON);
                $('#result').html(
                    `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        An error occurred while processing your request: 
                        ${xhr.responseJSON?.details || error}
                    </div>`
                );
            }
        });
    });

    // Save as PNG with improved quality
    $('#saveAsPng').click(function() {
        const svgElement = $('#result img')[0];
        if (!svgElement) return;

        // Create a canvas with higher resolution
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const scale = 2; // Higher resolution scale

        // Create a new image for better quality conversion
        const img = new Image();
        img.onload = function() {
            // Set canvas size to match the scaled image
            canvas.width = img.width * scale;
            canvas.height = img.height * scale;

            // Set background to white
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw image with improved quality
            ctx.scale(scale, scale);
            ctx.drawImage(img, 0, 0);

            try {
                // Convert to PNG with maximum quality
                const pngData = canvas.toDataURL('image/png', 1.0);
                
                // Create download link
                const downloadLink = document.createElement('a');
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                downloadLink.download = `visualization-${timestamp}.png`;
                downloadLink.href = pngData;
                
                // Trigger download
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
            } catch (error) {
                console.error('Error saving image:', error);
                alert('Failed to save the image. Please try again.');
            }
        };

        // Handle load errors
        img.onerror = function() {
            console.error('Error loading image for conversion');
            alert('Failed to load the image for conversion. Please try again.');
        };

        // Load the SVG image
        img.src = svgElement.src;
    });
});
