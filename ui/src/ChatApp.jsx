import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Loader, Globe, Shield, CheckCircle, XCircle, AlertTriangle, Upload, FileText, X, LogOut, BookOpen, Brain, MessageSquare } from 'lucide-react';
import MessageFormatter from './components/MessageFormatter';
import QuizGenerator from './components/QuizGenerator';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Language Bridge Logo Component
const LanguageBridgeLogo = ({ className = "w-6 h-6", color = "currentColor" }) => (
  <svg viewBox="0 0 100 100" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Globe */}
    <circle cx="50" cy="50" r="35" stroke={color} strokeWidth="3" fill="none"/>
    <path d="M20 50 Q50 20 80 50 Q50 80 20 50" stroke={color} strokeWidth="2" fill="none"/>
    <path d="M50 15 L50 85" stroke={color} strokeWidth="2"/>
    <path d="M15 50 L85 50" stroke={color} strokeWidth="2"/>
    
    {/* Shield overlay */}
    <path 
      d="M50 25 L65 35 L65 55 Q65 65 50 75 Q35 65 35 55 L35 35 Z" 
      fill={color} 
      fillOpacity="0.3"
    />
    <path 
      d="M45 45 L48 50 L55 40" 
      stroke={color} 
      strokeWidth="2" 
      fill="none"
    />
  </svg>
);

const ChatApp = ({ currentUser, onLogout }) => {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "🌍🛡️ Hello! I'm your Language Bridge Assistant with Content Moderation. I can translate text from any language to English and check if it's appropriate. Send me a message in any language or upload a PDF file for grading!",
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // File handling functions
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
        setFilePreview({
          name: file.name,
          size: (file.size / 1024 / 1024).toFixed(2), // Size in MB
          type: file.type
        });
      } else {
        alert('Please select a PDF file only.');
        event.target.value = '';
      }
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:application/pdf;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  // Call backend API (/api/chat) - updated to handle file uploads
  const callAgent = async (userMessage, pdfBase64 = null) => {
    const url = `${API_BASE}/api/chat`;
    const payload = { 
      message: userMessage, 
      user_id: 'web-user',
      session_id: `session-${Date.now()}`,
      pdf_file: pdfBase64 // Add PDF data if available
    };
    const res = await axios.post(url, payload, { timeout: 60000 }); // Increased timeout for file processing
    return res.data;
  };

  const handleSendMessage = async () => {
    if ((!inputMessage.trim() && !selectedFile) || isLoading) return;

    let pdfBase64 = null;
    let messageText = inputMessage;
    
    // Handle file upload
    if (selectedFile) {
      try {
        pdfBase64 = await convertFileToBase64(selectedFile);
        if (!messageText.trim()) {
          messageText = `📄 Uploaded PDF: ${selectedFile.name}`;
        } else {
          messageText += ` 📄 (with PDF: ${selectedFile.name})`;
        }
      } catch (error) {
        console.error('Error converting file to base64:', error);
        alert('Error processing the PDF file. Please try again.');
        return;
      }
    }

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      hasFile: !!selectedFile,
      fileName: selectedFile?.name,
      fileSize: filePreview?.size
    };

    // Add user message
    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    
    // Clear file selection
    removeFile();
    setIsLoading(true);

    try {
      const output = await callAgent(currentMessage, pdfBase64);

      if (output.success) {
        console.log('API Response:', output);
        console.log('Bot response text:', output.bot_response);
        console.log('Bot response length:', output.bot_response ? output.bot_response.length : 0);
        
        const botMessage = {
          id: Date.now() + 1,
          text: output.bot_response || 'No response received',
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString(),
          translationInfo: output.translation_info,
          moderationInfo: output.moderation_info,
          finalApproved: output.final_approved,
          isBlocked: !output.final_approved,
          gradingResult: output.grading_result,
          explanation_result: output.explanation_result // New field for explanation results
        };

        console.log('Bot message object:', botMessage);
        setMessages(prev => [...prev, botMessage]);
      } else {
        // Handle API error
        const errorMessage = {
          id: Date.now() + 1,
          text: output.bot_response || 'Sorry, I encountered an error processing your message.',
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errText = error?.response?.data?.detail || error?.message || 'Sorry, I encountered an error. Please try again.';
      const errorMessage = {
        id: Date.now() + 1,
        text: `❌ Error: ${errText}`,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        text: "🌍🛡️ Hello! I'm your Language Bridge Assistant with Content Moderation. I can translate text from any language to English and check if it's appropriate. Send me a message in any language or upload a PDF file for grading!",
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
    // Clear any selected files
    removeFile();
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                <LanguageBridgeLogo className="w-6 h-6" color="white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-800">EdRoom Language Bridge</h1>
                <p className="text-sm text-gray-500">
                  Welcome, {currentUser?.firstName || 'User'}! • AI-Powered Educational Tools
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {activeTab === 'chat' && (
                <button
                  onClick={clearChat}
                  className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Clear Chat
                </button>
              )}
              <button
                onClick={onLogout}
                className="flex items-center space-x-2 px-4 py-2 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="px-6">
          <div className="flex space-x-1 border-b">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Chat & Translation</span>
            </button>
            <button
              onClick={() => setActiveTab('quiz')}
              className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'quiz'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Quiz Generator</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      {activeTab === 'chat' ? (
        <>
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar">
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} message-slide-in`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className={`flex items-start space-x-3 max-w-3xl ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}` }>
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.sender === 'user' 
                  ? 'bg-blue-500' 
                  : 'bg-gradient-to-br from-blue-600 to-purple-600'
              }`}>
                {message.sender === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <LanguageBridgeLogo className="w-4 h-4" color="white" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={`rounded-2xl px-5 py-4 message-bubble message-content ${
                message.sender === 'user'
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-tr-md shadow-lg'
                  : message.isBlocked
                  ? 'bg-red-50 text-red-800 rounded-tl-md shadow-sm border border-red-200'
                  : message.isError
                  ? 'bg-orange-50 text-orange-800 rounded-tl-md shadow-sm border border-orange-200'
                  : 'bg-white text-gray-800 rounded-tl-md shadow-lg border border-gray-100'
              }`}>
                {/* File indicator for user messages */}
                {message.sender === 'user' && message.hasFile && (
                  <div className="flex items-center mb-2">
                    <FileText className="w-3 h-3 mr-1 text-blue-200" />
                    <span className="text-xs text-blue-200">
                      {message.fileName} ({message.fileSize} MB)
                    </span>
                  </div>
                )}

                {/* Simplified status indicators - only show what users need */}
                {message.sender === 'bot' && !message.isError && message.isBlocked && (
                  <div className="flex items-center mb-2">
                    <div className="flex items-center text-red-600">
                      <XCircle className="w-3 h-3 mr-1" />
                      <span className="text-xs font-medium">Message filtered for safety</span>
                    </div>
                  </div>
                )}

                <MessageFormatter message={message} isUser={message.sender === 'user'} />
                
                {/* Hide technical details - users don't need to see moderation/translation metrics */}

                <p className={`${
                  message.sender === 'user' 
                    ? 'text-blue-100' 
                    : message.isBlocked 
                    ? 'text-red-400' 
                    : message.isError
                    ? 'text-orange-400'
                    : 'text-gray-400'
                } text-xs mt-2`}>
                  {message.timestamp}
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* Enhanced Loading indicator */}
        {isLoading && (
          <div className="flex justify-start message-slide-in">
            <div className="flex items-start space-x-3 max-w-3xl">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                <LanguageBridgeLogo className="w-4 h-4" color="white" />
              </div>
              <div className="bg-white text-gray-800 rounded-2xl rounded-tl-md px-5 py-4 shadow-lg border border-gray-100 message-bubble">
                <div className="flex items-center space-x-3">
                  <Loader className="w-5 h-5 animate-spin text-blue-500" />
                  <span className="text-sm text-gray-600 font-medium">AI is thinking...</span>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full typing-dot"></div>
                  </div>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Processing your message...
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t px-6 py-4">
        {/* File Preview */}
        {filePreview && (
          <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-800">{filePreview.name}</p>
                  <p className="text-xs text-blue-600">{filePreview.size} MB • PDF Document</p>
                </div>
              </div>
              <button
                onClick={removeFile}
                className="p-1 hover:bg-blue-100 rounded"
                disabled={isLoading}
              >
                <X className="w-4 h-4 text-blue-600" />
              </button>
            </div>
          </div>
        )}

        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedFile ? "Add a message (optional)..." : "Type your message in any language or upload a PDF file..."}
              className="w-full px-4 py-3 border border-gray-300 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="1"
              style={{ minHeight: '48px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          
          {/* File Upload Button */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={isLoading}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className={`p-3 rounded-full transition-all ${
              isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gray-100 hover:bg-gray-200 active:bg-gray-300'
            }`}
            title="Upload PDF file"
          >
            <Upload className={`w-5 h-5 ${isLoading ? 'text-gray-500' : 'text-gray-600'}`} />
          </button>

          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={(!inputMessage.trim() && !selectedFile) || isLoading}
            className={`p-3 rounded-full transition-all ${
              (!inputMessage.trim() && !selectedFile) || isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700'
            }`}
          >
            <Send className={`w-5 h-5 ${(!inputMessage.trim() && !selectedFile) || isLoading ? 'text-gray-500' : 'text-white'}`} />
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-400 px-1">
          {isLoading 
            ? (selectedFile ? 'Processing PDF and message...' : 'Sending...') 
            : 'Enter to send, Shift+Enter for new line • Upload PDF files for grading'
          }
        </div>
      </div>
        </>
      ) : (
        /* Quiz Generator Tab */
        <div className="flex-1 overflow-y-auto">
          <QuizGenerator />
        </div>
      )}
    </div>
  );
};

export default ChatApp;
