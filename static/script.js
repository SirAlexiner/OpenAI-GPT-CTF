// script.js

// Get references to HTML elements
const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const navigation = document.getElementById("nav-open");
const header = document.getElementById("header-show");

// Add a resize event listener to change navigation style based on window width
window.addEventListener("resize", (event) => {
    if (window.innerWidth < 900) {
        navigation.id = 'nav-closed';
    } else {
        navigation.id = 'nav-open';
    }
});

// Function to append a chat message with a specified type (user or assistant)
function appendMessage(message, messageType) {
    const messageDiv = document.createElement("div");
    messageDiv.className = messageType;

    // Create elements for user avatar and message content
    const imageDiv = document.createElement("div");
    imageDiv.className = messageType + "-image";
    messageDiv.appendChild(imageDiv);

    // Add user avatar
    const userImage = document.createElement("img");
    userImage.src = "../static/user-image.png";
    imageDiv.appendChild(userImage);

    const messageDivChild = document.createElement("div");
    messageDivChild.className = messageType + "-content";
    messageDiv.appendChild(messageDivChild);

    // Set the message content
    messageDivChild.innerHTML = `${message}`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to open/close navigation
function closeOpenNavigation() {
    if (navigation.getAttribute('id') == "nav-open") {
        navigation.id = "nav-closed";
    } else {
        navigation.id = "nav-open";
    }
}

// Store the last scroll position for handling header visibility
let lastScrollPosition = chatMessages.scrollTop;
let isScrollingUp = false;

// Function to check if userInput is disabled
function isUserInputDisabled() {
    return userInput.disabled; // If userInput is an HTML input element
}

// Function to handle scrolling and show/hide header based on scroll direction
function handleScroll() {
    const currentScrollPosition = chatMessages.scrollTop;

    if (currentScrollPosition < lastScrollPosition) {
        isScrollingUp = true;
    } else if (currentScrollPosition > lastScrollPosition) {
        isScrollingUp = false;
    }

    if (!isUserInputDisabled() && isScrollingUp) {
        header.id = "header-show";
    } else {
        header.id = "header-hide";
    }

    lastScrollPosition = currentScrollPosition;
}

// Add a scroll event listener to the chat messages
chatMessages.addEventListener("scroll", handleScroll);

// Add a wheel event listener to prevent scrolling during GPT typing
chatMessages.addEventListener("wheel", function (event) {
    if (isUserInputDisabled()) {
        event.preventDefault();
    }
});

// Function to automatically resize the input textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight - 37, 200) + 'px';
    if (Math.min(textarea.scrollHeight - 37, 200) == 200) {
        textarea.style.overflowY = 'auto';
    } else {
        textarea.style.overflowY = 'hidden';
    }
}

function fadeIn(element) {
    element.style.opacity = 1;
}

function fadeOut(element) {
    element.style.opacity = 0;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Function to copy code to clipboard
async function copyCode(element) {
    if (!isUserInputDisabled()) {
        const code = element.parentElement.parentElement.querySelector('code');
        const textarea = document.createElement('textarea');
        textarea.value = code.innerText;
        document.body.appendChild(textarea);
        if (!navigator.clipboard) {
            textarea.select();
            document.execCommand('copy');
        } else {
            navigator.clipboard.writeText(textarea.value).then(
                async function () {
                    fadeOut(element);

                    setTimeout(() => {
                        element.innerHTML = '<span class="material-symbols-outlined">done</span>Copied!';
                        fadeIn(element);
                    }, 250);
                    await delay(2500);
                    fadeOut(element);

                    setTimeout(() => {
                        element.innerHTML = '<span class="material-symbols-outlined">content_paste</span>Copy Code';
                        fadeIn(element);
                    }, 250);
                })
                .catch(
                    function () {
                        alert("err"); // error
                    });
        }
        document.body.removeChild(textarea);
    }
}

// Define a custom renderer for marked.js
const customRenderer = new marked.Renderer();

// Override the code rendering method to add Prism.js syntax highlighting
customRenderer.code = function (code, language) {
    if (!language) {
        // Handle code blocks without specified language (default to plaintext)
        language = 'plaintext';
    }
    let highlightedCode = ""
    try {
        highlightedCode = Prism.highlight(code, Prism.languages[language], language);
    } catch (error) {
        highlightedCode = Prism.highlight(code, Prism.languages['plaintext'], 'plaintext');
    }

    return `<div class="code-block"><div class="code-header"><span class="language">${language}</span><button class="code-copy" onclick="copyCode(this)"><span class="material-symbols-outlined">content_paste</span>Copy Code</button></div><pre class="language-${language}"><code>${highlightedCode}</code></pre></div>`;
};

// Function to format GPT responses from Markdown to HTML using marked.js
function formatToHTML(markdownText) {
    // Use marked.js with the custom renderer
    return marked.parse(markdownText, { renderer: customRenderer });
}

// Function to handle user input and fetch a response from the Flask server
async function handleUserInput() {
    userInput.disabled = true;
    const userMessage = userInput.value.trim();

    if (userMessage !== "") {
        // Append the user message to the chat
        appendMessage(formatToHTML(userMessage), "user-message");
        userInput.value = "";
        userInput.style.height = 'auto';
        userInput.style.overflowY = 'hidden';

        // Encode user input
        const encodedInput = encodeURIComponent(userMessage);

        // Fetch a response from the Flask server
        const data = await fetch(`/get?input=${encodedInput}`)
            .then(response => response.json());

        const response = await fetch("/send", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        const decoder = new TextDecoder();

        const reader = response.body.getReader();

        // Create a message div for the assistant
        const messageDiv = document.createElement("div");
        messageDiv.className = "assistant-message";
        chatMessages.appendChild(messageDiv);

        const imageDiv = document.createElement("div");
        imageDiv.className = "assistant-message-image";
        messageDiv.appendChild(imageDiv);

        const botImage = document.createElement("img");
        botImage.src = "../static/bot-image.png";
        imageDiv.appendChild(botImage);

        const messageDivChild = document.createElement("div");
        messageDivChild.className = "assistant-message-content";
        messageDiv.appendChild(messageDivChild);

        let count = 0;
        let previousContent = '';
        let gptResponse = "";
        while (true) {
            if (userInput.value.length > 3) {
                userInput.value = "•";
            } else if (count % 5 == 0) {
                userInput.value += "•";
            }

            const { done, value } = await reader.read();
            if (done) {
                userInput.value = "";
                userInput.disabled = false;
                break;
            }

            const decodedValue = decoder.decode(value);

            // Display only if the content has changed
            if (decodedValue !== previousContent) {
                gptResponse += decodedValue; // Convert to HTML
                // Check if the latest message matches the last displayed message
                const lastDisplayedMessage = messageDivChild.innerHTML.trim();
                if (formatToHTML(gptResponse).trim() !== lastDisplayedMessage) {
                    messageDivChild.innerHTML = formatToHTML(gptResponse); // Set HTML content
                    previousContent = decodedValue; // Update previous content
                    chatMessages.scrollTo(0, chatMessages.scrollHeight);
                }
            }
        }
        userInput.focus();
    }
}

// Add an event listener for handling user input submission
userInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleUserInput();
    }
});