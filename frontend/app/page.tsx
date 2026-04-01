"use client";

import React, { useEffect, useState } from "react";
import { fetchFolders } from "@/services/emailService";

const BACKEND_API_URL = "http://localhost:8001";

type SyncedEmail = {
  id: string;
  subject: string;
  sender: string;
  sender_email: string;
  body: string;
  summary: string;
  action_items: string;
  priority: string;
  received_time: string;
};

export default function OutlookAgentPage() {
  const inboxOption = "Inbox";
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  const [folders, setFolders] = useState<string[]>([]);
  const [foldersLoading, setFoldersLoading] = useState(true);
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);

  // Set initial state to "Never" so it is always visible on the screen
  const [lastSyncTime, setLastSyncTime] = useState("Never");

  const [chatHistory, setChatHistory] = useState<
    { role: string; text: string; isCached?: boolean }[]
  >([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [syncedEmails, setSyncedEmails] = useState<SyncedEmail[]>([]);
  const [dbEmailTotal, setDbEmailTotal] = useState(0);
  const [showSyncedEmails, setShowSyncedEmails] = useState(false);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState("");

  useEffect(() => {
    const loadFolders = async () => {
      setFoldersLoading(true);
      try {
        const data = await fetchFolders();
        const nextFolders = [inboxOption, ...data.folders];
        setFolders(nextFolders);
        setSelectedFolders((current) =>
          current.length > 0 ? current : [inboxOption],
        );
      } catch (err) {
        console.error("Folder load error:", err);
        setSyncMessage("Failed to load Inbox folders.");
      } finally {
        setFoldersLoading(false);
      }
    };

    void loadFolders();
  }, []);

  const handleSync = async () => {
    if (selectedFolders.length === 0) {
      setSyncMessage("Select at least one Inbox folder before syncing.");
      return;
    }

    setSyncLoading(true);
    try {
      const response = await fetch(`${BACKEND_API_URL}/api/sync_emails`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_names: selectedFolders }),
      });
      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.detail || "Failed to sync emails.";
        throw new Error(errorMessage);
      }

      setSyncMessage(`${data.message} (${data.count} new emails found)`);
      // Save current time upon successful sync
      setLastSyncTime(new Date().toLocaleTimeString());
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to sync emails.";
      setSyncMessage(message);
    } finally {
      setSyncLoading(false);
    }
  };

  const handleFolderSelection = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const nextSelectedFolders = Array.from(
      event.target.selectedOptions,
      (option) => option.value,
    );
    setSelectedFolders(nextSelectedFolders);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || chatLoading) return;

    const trimmedInput = input.trim();
    const userMsg = { role: "user", text: trimmedInput };
    setChatHistory((prev) => [...prev, userMsg]);
    setInput("");
    setChatLoading(true);

    try {
      const historyForApi = chatHistory.map((message) => ({
        role: message.role === "bot" ? "assistant" : "user",
        content: message.text,
      }));

      const response = await fetch(`${BACKEND_API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: trimmedInput, history: historyForApi }),
      });
      const rawText = await response.text();
      let data: { answer?: string; detail?: string; is_cached?: boolean };

      try {
        data = rawText ? JSON.parse(rawText) : {};
      } catch {
        throw new Error(
          rawText
            ? `Server returned a non-JSON response: ${rawText.slice(0, 200)}`
            : "Server returned an empty response.",
        );
      }

      if (!response.ok) {
        const errorMessage = data.detail || "Chat API error.";
        throw new Error(errorMessage);
      }

      const botMsg = {
        role: "bot",
        text: data.answer,
        isCached: data.is_cached,
      };
      setChatHistory((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "bot",
          text:
            err instanceof Error
              ? `Error connecting to the server: ${err.message}`
              : "Error connecting to the server.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const fetchSyncedEmails = async () => {
    const urls = [
      `${BACKEND_API_URL}/emails/db?limit=10`,
      "http://localhost:8001/emails/db?limit=10",
    ];

    let lastError = "Failed to load synced emails.";

    for (const url of urls) {
      try {
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
          lastError = data.error || "Failed to load synced emails.";
          continue;
        }

        setSyncedEmails(data.emails ?? []);
        setDbEmailTotal(data.total ?? 0);
        setDbError("");
        return;
      } catch (error) {
        lastError =
          error instanceof Error ? error.message : "Failed to load synced emails.";
      }
    }

    throw new Error(lastError);
  };

  const handleViewSyncedEmails = async () => {
    if (showSyncedEmails) {
      setShowSyncedEmails(false);
      return;
    }

    setDbLoading(true);
    try {
      await fetchSyncedEmails();
      setShowSyncedEmails(true);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load synced emails.";
      setDbError(message);
      setShowSyncedEmails(true);
    } finally {
      setDbLoading(false);
    }
  };

  return (
    <main className="max-w-3xl mx-auto p-6 flex flex-col h-screen font-sans bg-[#0a0a0a] text-gray-200">
      <div className="flex flex-col h-full border border-gray-600 rounded-xl p-6 bg-[#111111] shadow-2xl">
        {/* Header & Sync Control Section */}
        {/* Added gap-6 to force space between text and button, flex-wrap prevents overlapping on narrow screens */}
        <header className="flex flex-wrap items-center justify-between gap-6 border-b border-gray-600 pb-4 mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-extrabold text-white tracking-wide">
              Outlook Email Agent
            </h1>
            {/* Applied same color/size to the text container and arranged vertically */}
            <div className="text-sm text-gray-400 mt-2 flex flex-col gap-1">
              <span>{syncMessage || "Ready to sync."}</span>
              {/* Removed the conditional rendering so it always displays */}
              <span>Last synced: {lastSyncTime}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-start gap-3">
            <div className="flex flex-col gap-2">
              <select
                multiple
                value={selectedFolders}
                onChange={handleFolderSelection}
                disabled={syncLoading || foldersLoading || folders.length === 0}
                className="min-w-52 rounded-md border border-gray-600 bg-[#0a0a0a] px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#00a651]"
                size={Math.min(Math.max(folders.length, 3), 8)}
              >
                {folders.length === 0 ? (
                  <option value="">
                    {foldersLoading ? "Loading folders..." : "No Inbox folders found"}
                  </option>
                ) : (
                  folders.map((folder) => (
                    <option key={folder} value={folder}>
                      {folder}
                    </option>
                  ))
                )}
              </select>
              <span className="text-xs text-gray-500">
                Ctrl/Cmd or Shift to select multiple folders
              </span>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={handleSync}
                disabled={syncLoading || foldersLoading || selectedFolders.length === 0}
                className={`px-5 py-2.5 rounded-md font-bold text-white whitespace-nowrap transition-colors ${
                  syncLoading || foldersLoading || selectedFolders.length === 0
                    ? "bg-gray-500 cursor-not-allowed"
                    : "bg-[#00a651] hover:bg-[#008f45]"
                }`}
              >
                {syncLoading ? "Syncing..." : "Sync New Emails"}
              </button>

              <button
                onClick={handleViewSyncedEmails}
                disabled={dbLoading}
                className={`px-5 py-2.5 rounded-md font-bold text-white whitespace-nowrap transition-colors ${
                  dbLoading
                    ? "bg-gray-500 cursor-not-allowed"
                    : "bg-slate-700 hover:bg-slate-600"
                }`}
              >
                {dbLoading
                  ? "Loading..."
                  : showSyncedEmails
                    ? "Hide Synced Emails"
                    : "View Synced Emails"}
              </button>
            </div>
          </div>
        </header>

        {showSyncedEmails && (
          <section className="mb-6 rounded-lg border border-gray-700 bg-[#161616] p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-white">Synced Emails</h2>
              <span className="text-sm text-gray-400">Total: {dbEmailTotal}</span>
            </div>

            {dbError ? (
              <div className="rounded-md border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
                {dbError}
              </div>
            ) : syncedEmails.length === 0 ? (
              <div className="rounded-md border border-gray-700 bg-[#101010] px-3 py-4 text-sm text-gray-400">
                No synced emails found.
              </div>
            ) : (
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {syncedEmails.map((email) => (
                  <article
                    key={email.id}
                    className="rounded-lg border border-gray-700 bg-[#101010] p-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="font-semibold text-white">{email.subject || "(No Subject)"}</h3>
                      <span className="text-xs text-gray-500">{email.received_time}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-300">{email.sender}</p>
                    <p className="mt-2 line-clamp-3 text-sm text-gray-400">
                      {email.summary || email.body || "No content available."}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Chat Display Area */}
        <div className="flex-1 overflow-y-auto bg-[#1a1a1a] p-4 rounded-lg mb-6 border border-gray-700 shadow-inner">
          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-2xl ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-[#2a2a2a] text-gray-100 border border-gray-600 rounded-bl-none shadow-sm"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.text}</p>

                {msg.isCached && (
                  <span className="inline-block mt-2 text-[10px] bg-[#3a3a00] text-yellow-400 px-2 py-0.5 rounded font-bold border border-yellow-700">
                    ⚡ CACHED
                  </span>
                )}
              </div>
            </div>
          ))}
          {chatLoading && (
            <div className="mb-4 flex justify-start">
              <div className="flex max-w-[80%] items-center gap-3 rounded-2xl rounded-bl-none border border-gray-600 bg-[#2a2a2a] p-3 text-gray-100 shadow-sm">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-500 border-t-white" />
                <div>
                  <p className="text-sm font-medium text-white">Searching emails...</p>
                  <p className="text-xs text-gray-400">
                    Searching synced emails and generating an answer.
                  </p>
                </div>
              </div>
            </div>
          )}
          {chatHistory.length === 0 && (
            <div className="h-full flex items-center justify-center text-gray-500">
              Send a message to start chatting with your Outlook Agent.
            </div>
          )}
        </div>

        {/* Input Field Section */}
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            placeholder="Ask a question about your emails..."
            disabled={chatLoading}
            className="flex-1 p-3 rounded-lg bg-[#0a0a0a] border border-gray-600 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-gray-500 disabled:cursor-not-allowed disabled:opacity-60"
          />
          <button
            onClick={handleSendMessage}
            disabled={chatLoading || !input.trim()}
            className="min-w-28 px-6 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors disabled:cursor-not-allowed disabled:bg-blue-900"
          >
            {chatLoading ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </main>
  );
}
