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

    // Create elements for user/assistant avatars and message content
    const imageDiv = document.createElement("div");
    imageDiv.className = messageType + "-image";
    messageDiv.appendChild(imageDiv);

    // Add user/assistant avatars
    const botImage = document.createElement("img");
    botImage.src = "../static/user-image.png"; // You might want to update this image source
    imageDiv.appendChild(botImage);

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

// Function to handle scrolling and show/hide header based on scroll direction
function handleScroll() {
    const currentScrollPosition = chatMessages.scrollTop;
    if (currentScrollPosition < lastScrollPosition) {
        header.id = "header-show";
    } else if (currentScrollPosition > lastScrollPosition) {
        header.id = "header-hide";
    }
    lastScrollPosition = currentScrollPosition;
}

// Add a scroll event listener to the chat messages
chatMessages.addEventListener("scroll", handleScroll);

// Function to automatically resize the input textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight-37, 200) + 'px';
    if (Math.min(textarea.scrollHeight-37, 200) == 200) {
        textarea.style.overflowY  = 'auto';
    } else {
        textarea.style.overflowY  = 'hidden';
    }
}

// Function to handle user input and fetch a response from the Flask server
async function handleUserInput() {
    userInput.disabled = true;
    const userMessage = userInput.value.trim();
    
    if (userMessage !== "") {
        // Append the user message to the chat
        appendMessage('<p>' + userMessage.replace(/\n/g, "<br>") + '</p>', "user-message");
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
        let chunks = "";

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
            messageDivChild.innerHTML = decoder.decode(value);
            count++;
            chatMessages.scrollTo(0, chatMessages.scrollHeight);
        }
    }
}

// Add an event listener for handling user input submission
userInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleUserInput();
    }
});