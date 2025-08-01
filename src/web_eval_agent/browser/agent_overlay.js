(function() {
    // --- Injection Guard ---
    if (window.__agentOverlayInjected === true) {
        // console.log('Agent overlay already injected or running, skipping.'); // Optional: reduce noise
        return;
    }
    // Set flag immediately to prevent race conditions
    window.__agentOverlayInjected = true;
    console.log('Setting injection flag.');

    try { // Start of try block wrapping the entire setup
        console.log('Agent control overlay script starting setup...');

        // --- Configuration ---
        const HOST_ELEMENT_ID = 'agent-control-host';
        const OVERLAY_ID = 'agent-control-overlay'; // ID inside shadow DOM

        // --- Cleanup existing host(s) ---
        const existingHosts = document.querySelectorAll('#' + HOST_ELEMENT_ID);
        existingHosts.forEach(host => {
            host.remove();
            console.log('Removed existing overlay host');
        });

        // --- Create Host Element in Main DOM ---
        const hostElement = document.createElement('div');
        hostElement.id = HOST_ELEMENT_ID;
        // Minimal host styling - just needs to exist to host the shadow DOM
        hostElement.style.cssText = `
            position: absolute; /* Or static, doesn't strictly matter */
            width: 0;
            height: 0;
            overflow: hidden;
            border: none;
            padding: 0;
            margin: 0;
        `;
        // NOTE: The overlay *inside* the shadow DOM uses its own fixed positioning relative to the viewport.

        if (document.body) {
            document.body.appendChild(hostElement);
            console.log('Added overlay host element to page body');
        } else {
            console.error('Cannot add overlay host: document.body is not available');
            // Wait for body to be available
            const hostBodyCheckInterval = setInterval(() => {
                if (document.body) {
                    document.body.appendChild(hostElement);
                    console.log('Added overlay host element to page body (delayed)');
                    clearInterval(hostBodyCheckInterval);
                }
            }, 100);
            // If body never appears, we can't proceed
            setTimeout(() => clearInterval(hostBodyCheckInterval), 5000);
            // If body isn't found, reset flag and exit
            window.__agentOverlayInjected = false;
            console.log('Resetting injection flag: body not found.');
            return;
        }

        // --- Attach Closed Shadow Root ---
        const shadowRoot = hostElement.attachShadow({ mode: 'closed' });
        console.log('Attached closed shadow root to host element');

        // --- Define Styles for Shadow DOM ---
        const styles = `
            #${OVERLAY_ID} {
                position: fixed; /* Position relative to viewport */
                top: 20px;       /* 20px from the top */
                left: 50%;       /* Left edge at 50% */
                transform: translateX(-50%); /* Shift left by half its width */
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                border-radius: 8px;
                padding: 10px;
                z-index: 2147483647; /* Higher than host */
                font-family: Arial, sans-serif;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
                min-width: 180px;
                box-sizing: border-box; /* Include padding in width/height */
            }
            .overlay-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                cursor: move;
                user-select: none; /* Prevent text selection during drag */
            }
            .overlay-title {
                font-weight: bold;
            }
            .minimize-btn {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                padding: 0 5px;
                line-height: 1; /* Ensure consistent height */
            }
            .overlay-content {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .agent-status {
                padding: 5px;
                text-align: center;
                border-radius: 4px;
                margin-bottom: 8px;
                font-size: 12px;
                background-color: #28a745; /* Default: Running */
            }
            .control-btn {
                padding: 8px 12px;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: opacity 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 5px; /* Space between icon and text */
            }
            .control-btn:hover {
                opacity: 0.85;
            }
            #pause-agent-btn { background-color: #ffc107; }
            #resume-agent-btn { background-color: #28a745; display: none; } /* Initially hidden */
            #stop-agent-btn { background-color: #dc3545; }
        `;

        // --- Inject Styles into Shadow Root ---
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        shadowRoot.appendChild(styleSheet);
        console.log('Injected styles into shadow root');

        // --- Create Overlay Structure Inside Shadow Root ---
        const overlay = document.createElement('div');
        overlay.id = OVERLAY_ID;

        // Header
        const header = document.createElement('div');
        header.className = 'overlay-header';
        const title = document.createElement('div');
        title.className = 'overlay-title';
        title.textContent = 'Agent Controls';
        const minimizeBtn = document.createElement('button');
        minimizeBtn.className = 'minimize-btn';
        minimizeBtn.innerHTML = '−';
        header.appendChild(title);
        header.appendChild(minimizeBtn);

        // Content
        const content = document.createElement('div');
        content.className = 'overlay-content';
        const statusIndicator = document.createElement('div');
        statusIndicator.className = 'agent-status';
        statusIndicator.id = 'agent-status-shadow'; // Unique ID within shadow DOM
        statusIndicator.textContent = 'Running';

        const pauseBtn = document.createElement('button');
        pauseBtn.id = 'pause-agent-btn-shadow';
        pauseBtn.className = 'control-btn';
        pauseBtn.innerHTML = '⏸️ Pause';
        pauseBtn.style.backgroundColor = '#ffc107'; // Set initial color via style

        const resumeBtn = document.createElement('button');
        resumeBtn.id = 'resume-agent-btn-shadow';
        resumeBtn.className = 'control-btn';
        resumeBtn.innerHTML = '▶️ Resume';
        resumeBtn.style.backgroundColor = '#28a745';
        resumeBtn.style.display = 'none'; // Initially hidden

        const stopBtn = document.createElement('button');
        stopBtn.id = 'stop-agent-btn-shadow';
        stopBtn.className = 'control-btn';
        stopBtn.innerHTML = '⏹️ Stop';
        stopBtn.style.backgroundColor = '#dc3545';

        content.appendChild(statusIndicator);
        content.appendChild(pauseBtn);
        content.appendChild(resumeBtn);
        content.appendChild(stopBtn);

        overlay.appendChild(header);
        overlay.appendChild(content);

        // --- Append Overlay to Shadow Root ---
        shadowRoot.appendChild(overlay);
        console.log('Appended overlay structure to shadow root');

        // --- Functionality (Listeners, etc.) ---

        // Minimize/maximize
        let isMinimized = false;
        minimizeBtn.addEventListener('click', () => {
            if (isMinimized) {
                content.style.display = 'flex';
                minimizeBtn.innerHTML = '−';
                isMinimized = false;
            } else {
                content.style.display = 'none';
                minimizeBtn.innerHTML = '+';
                isMinimized = true;
            }
        });

        // Draggable (using the host element for positioning calculations relative to viewport)
        makeDraggable(overlay, header); // Pass overlay element directly

        // Button listeners
        pauseBtn.addEventListener('click', async () => {
            try {
                if (typeof window.pauseAgent === 'function') {
                    await window.pauseAgent();
                    updateOverlayStatus('paused');
                } else { console.error('window.pauseAgent is not defined'); }
            } catch (e) { console.error('Failed to pause agent:', e); }
        });

        resumeBtn.addEventListener('click', async () => {
            try {
                 if (typeof window.resumeAgent === 'function') {
                    await window.resumeAgent();
                    updateOverlayStatus('running');
                 } else { console.error('window.resumeAgent is not defined'); }
            } catch (e) { console.error('Failed to resume agent:', e); }
        });

        stopBtn.addEventListener('click', async () => {
            try {
                 if (typeof window.stopAgent === 'function') {
                    await window.stopAgent();
                    updateOverlayStatus('stopped');
                 } else { console.error('window.stopAgent is not defined'); }
            } catch (e) { console.error('Failed to stop agent:', e); }
        });

        // Function to update the overlay status (operates on elements within shadow DOM)
        function updateOverlayStatus(status) {
            // Use shadowRoot.getElementById for elements inside the shadow DOM
            const statusEl = shadowRoot.getElementById('agent-status-shadow');
            const pauseBtnShadow = shadowRoot.getElementById('pause-agent-btn-shadow');
            const resumeBtnShadow = shadowRoot.getElementById('resume-agent-btn-shadow');
            const stopBtnShadow = shadowRoot.getElementById('stop-agent-btn-shadow');

            if (!statusEl || !pauseBtnShadow || !resumeBtnShadow || !stopBtnShadow) {
                console.error('Could not find all status elements within shadow DOM');
                return;
            }

            if (status === 'running') {
                statusEl.textContent = 'Running';
                statusEl.style.backgroundColor = '#28a745';
                pauseBtnShadow.style.display = 'flex'; // Use flex for consistency
                resumeBtnShadow.style.display = 'none';
                stopBtnShadow.style.display = 'flex'; // Ensure stop is visible when running
            } else if (status === 'paused') {
                statusEl.textContent = 'Paused';
                statusEl.style.backgroundColor = '#ffc107';
                pauseBtnShadow.style.display = 'none';
                resumeBtnShadow.style.display = 'flex';
                stopBtnShadow.style.display = 'flex'; // Ensure stop is visible when paused
            } else if (status === 'stopped') {
                statusEl.textContent = 'Stopped';
                statusEl.style.backgroundColor = '#dc3545';
                pauseBtnShadow.style.display = 'none';
                resumeBtnShadow.style.display = 'none';
                stopBtnShadow.style.display = 'none'; // Hide stop when stopped
            }
        }
        // Make update function globally accessible if needed by external calls (less likely now)
        // window.updateOverlayStatus = updateOverlayStatus; // Probably not needed

        // Check agent state periodically (relies on functions exposed on window)
        const stateCheckInterval = setInterval(async () => {
            try {
                if (typeof window.getAgentState === 'function') {
                    const state = await window.getAgentState();
                    if (state.stopped) {
                        updateOverlayStatus('stopped');
                        clearInterval(stateCheckInterval); // Stop checking if agent stopped
                    } else if (state.paused) {
                        updateOverlayStatus('paused');
                    } else {
                        updateOverlayStatus('running');
                    }
                } else {
                     // If function doesn't exist, stop checking
                     // console.warn('window.getAgentState not found, stopping state check.');
                     // clearInterval(stateCheckInterval);
                }
            } catch (e) {
                console.error('Failed to get agent state:', e);
                // clearInterval(stateCheckInterval); // Stop checking on error
            }
        }, 1000);

        // --- Helper Functions ---

        // Draggable function rewritten for correct positioning
        function makeDraggable(element, handle) {
            let startX = 0, startY = 0, initialElementX = 0, initialElementY = 0;

            handle.onmousedown = dragMouseDown;

            function dragMouseDown(e) {
                // Prevent default dragging behavior (e.g., text selection)
                e.preventDefault();
                // Get the mouse cursor position at startup
                startX = e.clientX;
                startY = e.clientY;

                // Get the element's initial position using getBoundingClientRect for accuracy
                const rect = element.getBoundingClientRect();
                initialElementX = rect.left;
                initialElementY = rect.top;

                // Ensure position is fixed and remove transform/conflicting styles
                // This ensures subsequent position updates use direct top/left
                element.style.transform = 'none';
                element.style.position = 'fixed';
                element.style.left = initialElementX + 'px'; // Set initial pixel value
                element.style.top = initialElementY + 'px';  // Set initial pixel value
                element.style.bottom = 'auto';
                element.style.right = 'auto';

                // Attach listeners to the document to capture mouse movements anywhere on the page
                document.addEventListener('mouseup', closeDragElement, true);
                document.addEventListener('mousemove', elementDrag, true);
            }

            function elementDrag(e) {
                e.preventDefault();
                // Calculate the distance the mouse has moved
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;

                // Calculate the new element position by adding the mouse delta to the initial position
                element.style.left = (initialElementX + dx) + 'px';
                element.style.top = (initialElementY + dy) + 'px';
            }

            function closeDragElement() {
                // Remove the listeners when the mouse button is released
                document.removeEventListener('mouseup', closeDragElement, true);
                document.removeEventListener('mousemove', elementDrag, true);
            }
        }

        // --- Patch elementFromPoint to ignore overlay ---
        // Keep references you’ll need inside the closure
        const host = hostElement;               // div#agent-control-host
        const panelRoot = shadowRoot;           // Reference the created shadowRoot

        // Utility: is a node somewhere inside the overlay?
        const isInsidePanel = node =>
            node === host ||
            (node && (host.contains(node) || (node.getRootNode() === panelRoot)));

    // Patch elementFromPoint / elementsFromPoint for Document and ShadowRoot ----

    // ---- generic helper that works on any root object ----
    function makeSafeElementFromPoint(root, origEFP, origEFPS) {
      // Note: We need the original EFP from the specific root's prototype
      const originalRootEFP = origEFP || root.elementFromPoint;
      return function safeEFP(x, y) {
        // `this` is the root (Document or ShadowRoot instance)
        let el = originalRootEFP.call(this, x, y); // Use call() with the correct context
        if (!isInsidePanel(el)) return el;

        const original = host.style.pointerEvents;
        host.style.pointerEvents = 'none';
        try   { el = originalRootEFP.call(this, x, y); } // Use call() again
        finally { host.style.pointerEvents = original; }
        return el;
      };
    }

    function makeSafeElementsFromPoint(root, origEFP, origEFPS) {
       // Note: We need the original EFPs from the specific root's prototype
      const originalRootEFP = origEFP || root.elementFromPoint;
      const originalRootEFPS = origEFPS || root.elementsFromPoint;
      // Fallback function using the single safe EFP if elementsFromPoint doesn't exist
      const fallbackEFP = makeSafeElementFromPoint(root, originalRootEFP, originalRootEFPS);

      return function safeEFPS(x, y) {
        // `this` is the root (Document or ShadowRoot instance)
        if (!originalRootEFPS) return [fallbackEFP.call(this, x, y)]; // Use call() for fallback

        const original = host.style.pointerEvents;
        host.style.pointerEvents = 'none';
        let elements = [];
        try {
          // Use call() with the correct context
          elements = originalRootEFPS.call(this, x, y).filter(el => !isInsidePanel(el));
        } finally {
          host.style.pointerEvents = original;
        }
        return elements;
      };
    }

    // ---- install on Document ----
    const docOrigEFP = document.elementFromPoint;
    const docOrigEFPS = document.elementsFromPoint;

    document.elementFromPoint = makeSafeElementFromPoint(document, docOrigEFP, docOrigEFPS);
    console.log('Patched document.elementFromPoint');

    if (docOrigEFPS) {
      document.elementsFromPoint = makeSafeElementsFromPoint(document, docOrigEFP, docOrigEFPS);
      console.log('Patched document.elementsFromPoint');
    }

    // ---- install on *all* ShadowRoots (via prototype) ----
    if (typeof ShadowRoot !== "undefined" && ShadowRoot.prototype) {
      const SRproto = ShadowRoot.prototype;
      const protoOrigEFP = SRproto.elementFromPoint; // Get originals from prototype
      const protoOrigEFPS = SRproto.elementsFromPoint;

      // Patch prototype methods
      SRproto.elementFromPoint = makeSafeElementFromPoint(SRproto, protoOrigEFP, protoOrigEFPS);
      console.log('Patched ShadowRoot.prototype.elementFromPoint');

      if (protoOrigEFPS) {
        SRproto.elementsFromPoint = makeSafeElementsFromPoint(SRproto, protoOrigEFP, protoOrigEFPS);
        console.log('Patched ShadowRoot.prototype.elementsFromPoint');
      }
    } else {
        console.warn('ShadowRoot prototype not available for patching.');
    }
    // --- End Patch ---

        // --- Ensure Host is Last Element (for stacking) ---
        (function bringPanelToFront() {
          const TARGET_ID = "playwright-highlight-container"; // ID used by buildDomTree.js

          // helper: put hostElement at the very end of <body>
          const moveHostToEnd = () => {
              if (document.body && hostElement.parentNode === document.body) {
                  document.body.appendChild(hostElement);
                  // console.log('Moved host element to end of body');
              } else if (document.body && hostElement.parentNode !== document.body) {
                  // If host somehow got detached, re-append it
                  document.body.appendChild(hostElement);
                  // console.log('Re-appended host element to end of body');
              }
          };

          // 1. if the highlight container already exists, just move once
          if (document.getElementById(TARGET_ID)) {
            moveHostToEnd();
            return;
          }

          // 2. otherwise observe <body> for that node, then move and stop.
          // Ensure body exists before observing
          if (!document.body) {
              console.warn('bringPanelToFront: document.body not ready for MutationObserver');
              // Optionally, retry after a short delay
              setTimeout(bringPanelToFront, 100);
              return;
          }

          const obs = new MutationObserver(muts => {
            for (const m of muts) {
              for (const n of m.addedNodes) {
                // Check nodeType just in case non-elements are added
                if (n.nodeType === Node.ELEMENT_NODE && n.id === TARGET_ID) {
                  moveHostToEnd();
                  obs.disconnect();
                  // console.log('Disconnected highlight container observer');
                  return;
                }
              }
            }
          });

          obs.observe(document.body, { childList: true });
          // console.log('Observing body for highlight container');

          // Optional: Timeout to stop observing if highlight container never appears
          setTimeout(() => {
              obs.disconnect();
              // console.log('Timeout reached for highlight container observer');
          }, 10000); // Stop observing after 10 seconds

        })();
        // --- End Stacking Fix ---

        console.log('Agent overlay setup complete.'); // End of successful try block logic

    } catch (error) { // Catch block Start
        console.error('Error during agent overlay setup:', error);
        // Reset flag on error to allow retry on next injection attempt
        window.__agentOverlayInjected = false;
        console.log('Resetting injection flag due to error.');
    } // Catch block End

})(); // End of main IIFE
