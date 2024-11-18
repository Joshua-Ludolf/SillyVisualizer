// Init panzoom
    $(document).ready(function() {
            // Initialize Panzoom on the #result container for image rendering
            const panzoomInstance = panzoom(document.querySelector('#result'), {
                zoomSpeed: 0.1, // Controls the zoom speed
                minZoom: 0.1,   // Minimum zoom level (don't allow zooming out too far)
                maxZoom: 5,     // Maximum zoom level (don't allow zooming in too far)
                contain: 'outside', // Prevents the content from overflowing the container
            });

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

            // // Initialize panzoom
            // function initPanzoom() {
            //     const element = document.querySelector('#result');
            //     if (element && !panzoomInstance) {
            //         panzoomInstance = panzoom(element, {
            //             maxZoom: 5,
            //             minZoom: 0.1,
            //             bounds: true,
            //             boundsPadding: 0.1
            //         });
            //     }
            // }

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

            // Zoom controls
            // $('#zoomIn').click(() => panzoomInstance && panzoomInstance.zoomIn());
            // $('#zoomOut').click(() => panzoomInstance && panzoomInstance.zoomOut());
            // $('#resetZoom').click(() => {
            //     if (panzoomInstance) {
            //         panzoomInstance.reset();
            //         panzoomInstance.moveTo(0, 0);
            //     }
            // });

            // Zoom controls updated 11-18-2024
            // zoomIn function; Increases zoom
            $('#zoomIn').click(function() {
                panzoomInstance.zoomIn()
            });
            // zoomOut function; Decreases zoom
            $('#zoomOut').click(function () {
                panzoomInstance.zoomOut();
            });
            // resetZoom function; Reset to zoom 1
            $('#resetZoom').click(function () {
                panzoomInstance.reset();
            });
            // panning function
            $('#result').on('mousedown', function (e) {
                panzoomInstance.panTo(e.pageX, e.pageY);
            });


            // Save as PNG
            $('#saveAsPng').click(function() {
                const img = $('#result img');
                if (img.length) {
                    const link = document.createElement('a');
                    link.download = 'visualization.png';
                    link.href = img.attr('src');
                    document.body.appendChild(link);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            });

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
                                `<img src="${response.image}" alt="Code Visualization" />`
                            );

                            // Initialize panzoom after image is loaded
                            $('#result img').on('load', function() {
                                initPanzoom();
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
        });
