(function(window, document) {
    const LOCAL_SCRIPTS = [
        'vendor/blockly/blockly_compressed.js',
        'vendor/blockly/blocks_compressed.js',
        'vendor/blockly/msg/en.js'
    ];

    const CDN_SCRIPTS = [
        'https://unpkg.com/blockly@12.3.1/blockly.min.js'
    ];

    const SUPPORT_SCRIPTS = [
        'robot_blocks.js',
        'robot_generator.js'
    ];

    function loadScriptsSequentially(sources, onSuccess, onFailure) {
        const total = sources.length;
        let index = 0;

        function next() {
            if (index >= total) {
                onSuccess();
                return;
            }
            const script = document.createElement('script');
            script.src = sources[index];
            script.async = false;
            script.onload = function() {
                index += 1;
                next();
            };
            script.onerror = function(event) {
                script.remove();
                onFailure(sources[index]);
            };
            document.head.appendChild(script);
        }

        next();
    }

    function finalize() {
        loadScriptsSequentially(SUPPORT_SCRIPTS, function() {
            window.dispatchEvent(new Event('RobotBlocklyReady'));
        }, function(failedSource) {
            console.error('Failed to load Blockly support script:', failedSource);
        });
    }

    function startLoading() {
        loadScriptsSequentially(LOCAL_SCRIPTS, finalize, function() {
            console.warn('Local Blockly bundles not found. Falling back to CDN.');
            loadScriptsSequentially(CDN_SCRIPTS, finalize, function(failed) {
                console.error('Unable to load Blockly from CDN:', failed);
                window.dispatchEvent(new Event('RobotBlocklyFailed'));
            });
        });
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        startLoading();
    } else {
        document.addEventListener('DOMContentLoaded', startLoading);
    }
})(window, document);
