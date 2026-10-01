import React from "react";

function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      <div className={`avatar ${isUser ? "user-avatar" : "bot-avatar"}`}>
        {isUser ? "👤" : "🤖"}
      </div>

      <div className="message-content">
        <div className="message-name">
          {isUser ? "You" : "AI Assistant"}
        </div>

        <div className={`message-bubble ${isUser ? "user-message" : ""}`}>
          {message.content}
        </div>

        {message.tools_used && message.tools_used.length > 0 && (
          <div className="used-tools">
            <div className="used-tools-title">
              🛠️ Tools used
            </div>

            {message.tools_used.map((tool, index) => (
              <div className="tool-result" key={index}>
                <strong>{tool.name}</strong>

                <pre>{tool.result}</pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;