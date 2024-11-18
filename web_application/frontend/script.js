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

    // Language detection
    function detectLanguage(code) {
        const pythonIndicators = ['def ', 'import ', 'print(', '__init__', 'self.'];
        const javaIndicators = ['public class', 'private ', 'void ', 'String[]', ';'];

        let pythonScore = pythonIndicators.filter(ind => code.includes(ind)).length;
        let javaScore = javaIndicators.filter(ind => code.includes(ind)).length;

        return pythonScore >= javaScore ? 'python' : 'java';
    }

    // Advanced Diagram Interaction
    function setupDiagramInteraction() {
        const $resultContainer = $('#result');
        const $image = $resultContainer.find('img');

        // Ensure the container has a relative position for proper zooming
        $resultContainer.css({
            'position': 'relative',
            'overflow': 'hidden',
            'width': '100%',
            'height': '500px'  // Fixed height with scrolling
        });

        // Initial state
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX, startY;

        // Apply initial transform
        function updateTransform() {
            $image.css('transform', `translate(${translateX}px, ${translateY}px) scale(${scale})`);
        }

        // Zoom functionality
        function zoom(delta, clientX, clientY) {
            const rect = $resultContainer[0].getBoundingClientRect();
            const mouseX = clientX - rect.left;
            const mouseY = clientY - rect.top;

            // Calculate zoom factor
            const zoomFactor = delta > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.5, Math.min(5, scale * zoomFactor));

            // Calculate translation to zoom towards mouse point
            const dx = (mouseX - translateX) * (1 - newScale / scale);
            const dy = (mouseY - translateY) * (1 - newScale / scale);

            translateX += dx;
            translateY += dy;
            scale = newScale;

            updateTransform();
        }

        // Pan functionality
        function startPan(clientX, clientY) {
            isDragging = true;
            startX = clientX - translateX;
            startY = clientY - translateY;
            $resultContainer.css('cursor', 'grabbing');
        }

        function pan(clientX, clientY) {
            if (!isDragging) return;

            translateX = clientX - startX;
            translateY = clientY - startY;
            updateTransform();
        }

        function stopPan() {
            isDragging = false;
            $resultContainer.css('cursor', 'grab');
        }

        // Event Listeners
        $resultContainer.on('wheel', function(e) {
            e.preventDefault();
            zoom(e.originalEvent.deltaY, e.clientX, e.clientY);
        });

        $resultContainer.on('mousedown touchstart', function(e) {
            e.preventDefault();
            const clientX = e.type === 'touchstart' 
                ? e.originalEvent.touches[0].clientX 
                : e.clientX;
            const clientY = e.type === 'touchstart' 
                ? e.originalEvent.touches[0].clientY 
                : e.clientY;
            
            startPan(clientX, clientY);
        });

        $(document).on('mousemove touchmove', function(e) {
            if (!isDragging) return;
            e.preventDefault();
            
            const clientX = e.type === 'touchmove' 
                ? e.originalEvent.touches[0].clientX 
                : e.clientX;
            const clientY = e.type === 'touchmove' 
                ? e.originalEvent.touches[0].clientY 
                : e.clientY;
            
            pan(clientX, clientY);
        });

        $(document).on('mouseup touchend', function() {
            stopPan();
        });

        // Reset zoom button
        $('#resetZoom').on('click', function() {
            scale = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        });

        // Zoom controls for + and - buttons
        $('#zoomIn').on('click', function() {
            const $resultContainer = $('#result');
            const $image = $resultContainer.find('img');
            
            // Get the center of the container
            const rect = $resultContainer[0].getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Zoom in (decrease negative value to zoom in)
            zoom(-1, centerX, centerY);
        });

        $('#zoomOut').on('click', function() {
            const $resultContainer = $('#result');
            const $image = $resultContainer.find('img');
            
            // Get the center of the container
            const rect = $resultContainer[0].getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Zoom out (increase positive value to zoom out)
            zoom(1, centerX, centerY);
        });

        // Initial setup
        $resultContainer.css('cursor', 'grab');
        $image.css('transition', 'transform 0.2s ease');
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

        const reader = new FileReader();
        reader.onload = function(e) {
            const code = e.target.result;
            $('#codeEditor').val(code);

            if ($('#language').val() === 'auto') {
                const detectedLang = detectLanguage(code);
                $('#language').val(detectedLang);
            }
        };
        reader.readAsText(file);
    }

    // Form submission
    $('#codeForm').submit(function(e) {
        e.preventDefault();

        // Reset and show loading state
        $('#loading').removeClass('hidden');
        $('#result').empty();
        $('#codeStats').addClass('hidden');
        $('#saveAsPng').addClass('hidden');

        // Clear any existing panzoom instance
        if (panzoomInstance) {
            panzoomInstance.dispose();
            panzoomInstance = null;
        }

        const formData = new FormData(this);
        const code = $('#codeEditor').val();

        if (code) {
            if (formData.get('language') === 'auto') {
                formData.set('language', detectLanguage(code));
            }
            formData.set('code', code);
        }

        $.ajax({
            url: '/visualize',
            type: 'post',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#loading').addClass('hidden');

                if (response.error) {
                    $('#result').html(
                        `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            ${response.error}
                        </div>`
                    );
                } else {
                    // Display visualization
                    $('#result').html(
                        `<img src="${response.image}" alt="Code Visualization" style="max-width: 100%; height: auto;">`
                    );

                    // Wait for image to load before setting up interaction
                    $('#result img').on('load', function() {
                        setupDiagramInteraction();
                        $('#saveAsPng').removeClass('hidden');
                    });

                    // Update code statistics if available
                    if (response.code_stats) {
                        $('#codeStats').removeClass('hidden');
                        $('#linesOfCode').text(response.code_stats.lines_of_code);
                        $('#functionCount').text(response.code_stats.functions);
                        $('#classCount').text(response.code_stats.classes);
                        $('#charCount').text(response.code_stats.characters);
                    }
                }
            },
            error: function(xhr, status, error) {
                $('#loading').addClass('hidden');
                $('#result').html(
                    `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        An error occurred while processing your request: ${error}
                    </div>`
                );
            }
        });
    });

    // Save as PNG
    $('#saveAsPng').click(function() {
        const img = $('#result img');
        if (img.length) {
            const link = document.createElement('a');
            link.download = 'visualization.png';
            link.href = img.attr('src');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });
});
