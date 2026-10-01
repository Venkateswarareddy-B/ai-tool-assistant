
import React, { useState } from "react";

import Sidebar from "./components/Sidebar";
import ChatMessage from "./components/ChatMessage";
import ToolCard from "./components/ToolCard";

const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/+$/, "") ||
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

const toolExamples = {
  Weather: "What is the weather in Hyderabad?",
  Currency: "Convert 100 USD to INR",
  Wikipedia: "Tell me about artificial intelligence",
  Calculator: "Calculate 125 * 24 + 50",
  News: "Give me the latest news about artificial intelligence",
  Location: "Find the location of Hyderabad",
};

const toolData = [
  { name: "Weather", icon: "🌦️", description: "Get current weather" },
  { name: "Currency", icon: "💱", description: "Convert currencies" },
  { name: "Wikipedia", icon: "📚", description: "Search knowledge" },
  { name: "Calculator", icon: "🧮", description: "Calculate anything" },
  { name: "News", icon: "📰", description: "Get recent news" },
  { name: "Location", icon: "📍", description: "Find coordinates" },
];

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 I'm your AI Tool Assistant. I can use Weather, Currency, Wikipedia, Calculator, News and Location tools. What would you like to do?",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (customMessage = null) => {
    const messageToSend = (customMessage ?? input).trim();

    if (!messageToSend || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content: messageToSend },
    ]);

    setInput("");
    setLoading(true);

    try {
      if (!API_URL) {
        throw new Error("VITE_API_URL is not configured");
      }

      const response = await fetch(
        `${API_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: messageToSend,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || `Backend request failed: ${response.status}`
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer || "I couldn't generate a response.",
          tools_used: data.tools_used || [],
        },
      ]);
    } catch (error) {
      console.error("Chat API error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `❌ ${error instanceof Error ? error.message : "The chat request failed."}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleToolClick = (toolName) => {
    const example = toolExamples[toolName];
    if (example) setInput(example);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  return (
    <div className="app">
      <Sidebar onToolClick={handleToolClick} />

      <main className="chat-area">
        <header className="chat-header">
          <div>
            <h2>AI Tool Assistant</h2>
            <p>Ask questions and let AI choose the right tool</p>
          </div>

          <div className="connection-status">
            <span></span>
            Online
          </div>
        </header>

        <section className="messages">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}

          {loading && (
            <div className="message-row assistant-row">
              <div className="avatar bot-avatar">🤖</div>

              <div className="message-content">
                <div className="message-name">AI Assistant</div>
                <div className="message-bubble typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </section>

        {messages.length === 1 && (
          <section className="tools-section">
            <h3>Try a tool</h3>

            <div className="tool-grid">
              {toolData.map((tool) => (
                <ToolCard
                  key={tool.name}
                  name={tool.name}
                  icon={tool.icon}
                  description={tool.description}
                  onClick={() => handleToolClick(tool.name)}
                />
              ))}
            </div>
          </section>
        )}

        <div className="input-container">
          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask me anything..."
              disabled={loading}
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
            >
              {loading ? "..." : "➤"}
            </button>
          </form>

          <p className="input-hint">
            AI may use external tools to answer your question.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;