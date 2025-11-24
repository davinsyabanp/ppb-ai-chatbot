// Configure marked.js for proper Markdown rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    sanitize: false
});

// Generate or retrieve a unique session ID for this browser session
const sessionId = sessionStorage.getItem('chat_session_id') ||
    'web-user-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
sessionStorage.setItem('chat_session_id', sessionId);

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
let conversationHasStarted = false;
let isInitialGreetingSent = false;

/**
 * Send initial greeting message to start conversation
 */
async function sendInitialGreeting() {
    if (isInitialGreetingSent) return;
    setLoading(true);
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: "halo",
                user_id: sessionId,
                conversationHasStarted: false,
                isInitialGreetingSent: false
            })
        });
        const data = await res.json();
        appendMessage(data.response, 'bot');
        isInitialGreetingSent = true;
    } catch (err) {
        appendMessage('Sorry, an error occurred while starting the conversation. Please reload the page.', 'bot');
    } finally {
        setLoading(false);
    }
}

/**
 * Append message to chat display
 * @param {string} text - Message text to display
 * @param {string} sender - 'bot' or 'user'
 */
function appendMessage(text, sender) {
    const row = document.createElement('div');
    row.className = `flex mb-3 ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

    if (sender === 'bot') {
        // Add avatar for bot messages
        const avatar = document.createElement('div');
        avatar.className = 'w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-slate-600 to-slate-700 rounded-full flex items-center justify-center overflow-hidden mr-2 flex-shrink-0 shadow-md border border-white/20';
        avatar.innerHTML = '<img src="/static/images/PPBOT_Logo.png" alt="PPBOT Avatar" class="w-full h-full object-cover">';
        row.appendChild(avatar);
    }

    const content = document.createElement('div');
    
    // Apply base classes
    const baseClasses = `rounded-xl py-2 px-3 max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl text-sm sm:text-base shadow-md`;
    const senderClasses = sender === 'user' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' : 'bg-white text-gray-800 border border-gray-100';
    content.className = `${baseClasses} ${senderClasses} break-words`;

    if (sender === 'bot') {
        // Parse Markdown content for bot messages
        const htmlContent = marked.parse(text, {
            gfm: true,
            breaks: true
        });
        
        content.innerHTML = htmlContent;
        content.classList.add('markdown-content');
    } else {
        // Plain text for user messages
        content.textContent = text;
    }

    row.appendChild(content);
    row.classList.add('message-enter');
    chatMessages.appendChild(row);
    
    // Add spacer after the last message
    const existingSpacer = chatMessages.querySelector('.message-spacer');
    if (existingSpacer) {
        existingSpacer.remove();
    }
    const spacer = document.createElement('div');
    spacer.className = 'h-4 message-spacer';
    chatMessages.appendChild(spacer);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show or hide loading indicator
 * @param {boolean} isLoading - True to show loading, false to hide
 */
function setLoading(isLoading) {
    let loadingEl = document.getElementById('loading-bot-msg');
    if (isLoading && !loadingEl) {
        const loadingRow = document.createElement('div');
        loadingRow.className = 'flex justify-start mb-3';
        loadingRow.id = 'loading-bot-msg';
        
        // Create avatar for loading message
        const avatar = document.createElement('div');
        avatar.className = 'w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-slate-600 to-slate-700 rounded-full flex items-center justify-center overflow-hidden mr-2 flex-shrink-0 shadow-md border border-white/20';
        avatar.innerHTML = '<img src="/static/images/PPBOT_Logo.png" alt="PPBOT Avatar" class="w-full h-full object-cover">';
        loadingRow.appendChild(avatar);
        
        loadingRow.innerHTML += `<div class="rounded-xl py-2 px-3 max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl bg-white text-gray-800 text-sm sm:text-base shadow-md border border-gray-100"><span class="animate-pulse">...</span></div>`;
        
        // Remove existing spacer before adding loading
        const existingSpacer = chatMessages.querySelector('.message-spacer');
        if (existingSpacer) {
            existingSpacer.remove();
        }
        
        chatMessages.appendChild(loadingRow);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else if (!isLoading && loadingEl) {
        loadingEl.remove();
        
        // Add spacer back after loading is done
        const spacer = document.createElement('div');
        spacer.className = 'h-4 message-spacer';
        chatMessages.appendChild(spacer);
    }
}

/**
 * Handle form submission for sending messages
 */
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;

    appendMessage(userMsg, 'user');
    chatInput.value = '';
    setLoading(true);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userMsg,
                user_id: sessionId,
                conversationHasStarted: conversationHasStarted,
                isInitialGreetingSent: isInitialGreetingSent
            })
        });
        const data = await res.json();
        appendMessage(data.response, 'bot');
        if (!conversationHasStarted) conversationHasStarted = true;
    } catch (err) {
        appendMessage('Maaf, terjadi kesalahan. Mohon coba lagi nanti.', 'bot');
    } finally {
        setLoading(false);
    }
});

/**
 * Initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Bot will greet when the user sends their first message
});
