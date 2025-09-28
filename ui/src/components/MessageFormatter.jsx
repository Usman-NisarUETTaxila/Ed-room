import React from 'react';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Globe, 
  Shield, 
  FileText, 
  Award, 
  BookOpen, 
  Brain,
  MessageCircle,
  Target,
  HelpCircle
} from 'lucide-react';

const MessageFormatter = ({ message, isUser = false }) => {
  // Utilities for structured formatting, JSON detection and code fences
  const stripCodeFences = (text) => {
    if (!text) return '';
    const trimmed = text.trim();
    // ```json ... ``` or ``` ... ```
    if (trimmed.startsWith('```')) {
      const firstLineEnd = trimmed.indexOf('\n');
      const fenceLang = trimmed.slice(3, firstLineEnd > -1 ? firstLineEnd : undefined).trim().toLowerCase();
      const inner = firstLineEnd > -1 ? trimmed.slice(firstLineEnd + 1) : '';
      const withoutClosing = inner.endsWith('```') ? inner.slice(0, -3) : inner;
      return withoutClosing.trim();
    }
    return trimmed;
  };

  const tryParseJSON = (text) => {
    if (!text) return null;
    // Normalize quotes
    const normalized = text
      .replace(/[\u201C\u201D]/g, '"')
      .replace(/[\u2018\u2019]/g, "'");
    try {
      // Quick heuristic: must start with { or [
      const t = normalized.trim();
      if (!(t.startsWith('{') || t.startsWith('['))) return null;
      return JSON.parse(t);
    } catch (e) {
      return null;
    }
  };

  const renderJSONBlock = (obj) => {
    let pretty = '';
    try {
      pretty = JSON.stringify(obj, null, 2);
    } catch {
      pretty = String(obj);
    }
    return (
      <pre className="text-xs md:text-sm leading-relaxed whitespace-pre-wrap bg-gray-900 text-green-400 border border-gray-300 rounded-lg p-4 overflow-x-auto shadow-inner font-mono">
        {pretty}
      </pre>
    );
  };

  // Enhanced function to parse and format text with better structure and line breaks
  const formatText = (text) => {
    if (!text) return '';
    
    // First, normalize line breaks and ensure proper spacing around headings
    let normalizedText = text
      // Ensure headings start on new lines
      .replace(/([.!?])\s*(\*\*[^*]+\*\*)/g, '$1\n\n$2')
      // Ensure sections are properly separated
      .replace(/(\*\*[^*]+\*\*)\s*([^\n*])/g, '$1\n\n$2')
      // Clean up multiple consecutive newlines
      .replace(/\n{3,}/g, '\n\n')
      .trim();
    
    // Split text by double newlines to create sections with better spacing
    const sections = normalizedText.split('\n\n');
    
    return sections.map((section, sectionIndex) => {
      // If the whole section looks like JSON (possibly inside code fences), pretty print it
      const candidate = stripCodeFences(section);
      const parsed = tryParseJSON(candidate);
      if (parsed !== null) {
        return (
          <div key={sectionIndex} className={sectionIndex > 0 ? 'mt-6' : ''}>
            {renderJSONBlock(parsed)}
          </div>
        );
      }

      // Check if this section is a main heading (starts with **)
      const isMainSection = section.trim().startsWith('**');
      const isHeadingSection = /^\*\*[^*]+\*\*$/.test(section.trim());
      
      // Split each section by single newlines
      const lines = section.split('\n');

      return (
        <div key={sectionIndex} className={`${
          sectionIndex > 0 ? (isMainSection ? 'mt-8' : 'mt-5') : ''
        } ${isMainSection && !isHeadingSection ? 'bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500' : ''}`}>
          {lines.map((line, lineIndex) => {
            if (!line.trim()) return null;

            // Horizontal separator
            if (line.trim().startsWith('===')) {
              return <div key={lineIndex} className="my-6 border-t-2 border-gray-300"></div>;
            }

            return (
              <div key={lineIndex}>
                {formatLine(line)}
              </div>
            );
          })}
        </div>
      );
    });
  };

  // Function to format individual lines with enhanced formatting and proper line breaks
  const formatLine = (line) => {
    const trimmed = line.trim();

    // Enhanced heading detection for **Bold Headings**
    if (/^\*\*[^*]+\*\*$/.test(trimmed)) {
      const headingText = trimmed.replace(/\*\*/g, '');
      return (
        <div className="text-xl font-bold text-gray-900 mt-8 mb-4 pb-3 border-b-2 border-blue-200 bg-gradient-to-r from-blue-50 to-transparent p-3 rounded-lg">
          {headingText}
        </div>
      );
    }

    // Sub-headings: **Text** within other content
    if (trimmed.includes('**') && !(/^\*\*[^*]+\*\*$/.test(trimmed))) {
      return (
        <div className="text-sm leading-relaxed mt-3 mb-2">
          {formatWithMarkdown(line)}
        </div>
      );
    }

    // Numbered list items: 1. item, 2. item, etc.
    if (/^\d+\.\s+/.test(trimmed)) {
      const match = trimmed.match(/^(\d+)\.(\s+)(.*)/);
      if (match) {
        return (
          <div className="text-sm leading-relaxed flex items-start mt-3 mb-1 pl-2">
            <span className="font-bold text-blue-600 mr-3 min-w-[24px] bg-blue-100 rounded-full w-6 h-6 flex items-center justify-center text-xs">
              {match[1]}
            </span>
            <span className="flex-1 pt-0.5">{formatWithMarkdown(match[3])}</span>
          </div>
        );
      }
    }

    // Simple list items: - item or * item or • item
    if (/^[-*•]\s+/.test(trimmed)) {
      return (
        <div className="text-sm leading-relaxed flex items-start mt-2 mb-1 pl-2">
          <span className="text-blue-500 mr-3 mt-1.5 font-bold">•</span>
          <span className="flex-1">{formatWithMarkdown(trimmed.replace(/^[-*•]\s+/, ''))}</span>
        </div>
      );
    }

    // Section headings: lines that end with a colon
    if (/^[^:]{2,80}:$/.test(trimmed)) {
      return (
        <div className="text-base font-bold text-gray-800 mt-6 mb-3 pb-1 border-b border-gray-300">
          {trimmed}
        </div>
      );
    }

    // Markdown-like bold support
    if (line.includes('**') || line.includes('*')) {
      return (
        <div className="text-sm leading-relaxed mt-2 mb-1">
          {formatWithMarkdown(line)}
        </div>
      );
    }

    // Regular text with proper spacing
    return (
      <div className="text-sm leading-relaxed mt-2 mb-1">
        {line}
      </div>
    );
  };

  // Function to handle markdown-like formatting
  const formatWithMarkdown = (text) => {
    const parts = [];
    let currentIndex = 0;
    
    // Regular expression to find **bold** text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the bold part
      if (match.index > currentIndex) {
        parts.push(
          <span key={`text-${currentIndex}`}>
            {text.substring(currentIndex, match.index)}
          </span>
        );
      }
      
      // Add the bold part with special styling based on content
      const boldContent = match[1];
      const boldElement = (
        <span key={`bold-${match.index}`} className={getBoldStyle(boldContent)}>
          {boldContent}
        </span>
      );
      parts.push(boldElement);
      
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(
        <span key={`text-${currentIndex}`}>
          {text.substring(currentIndex)}
        </span>
      );
    }
    
    return <div className="text-sm leading-relaxed">{parts}</div>;
  };
  

  // Function to get appropriate styling for bold text based on content
  const getBoldStyle = (content) => {
    const lowerContent = content.toLowerCase();
    
    // Apply rich styling for all languages - let the API handle content appropriateness
    // Grade-related content
    if (lowerContent.includes('grade:') || lowerContent.includes('your grade') || 
        lowerContent.includes('درجت') || lowerContent.includes('nota') || lowerContent.includes('calificación')) {
      return 'font-bold text-emerald-700 bg-emerald-100 px-3 py-2 rounded-lg text-lg';
    }
    
    // Performance indicators
    if (lowerContent.includes('performance:') || lowerContent.includes('الأداء') || 
        lowerContent.includes('rendimiento') || lowerContent.includes('performance')) {
      return 'font-bold text-blue-700 bg-blue-100 px-2 py-1 rounded-md';
    }
    
    // Feedback sections
    if (lowerContent.includes('feedback:') || lowerContent.includes('التعليقات') || 
        lowerContent.includes('comentarios') || lowerContent.includes('retour')) {
      return 'font-bold text-purple-700 bg-purple-100 px-2 py-1 rounded-md';
    }
    
    // Translation indicators
    if (lowerContent.includes('translated from') || lowerContent.includes('مترجم من') || 
        lowerContent.includes('traducido de')) {
      return 'font-bold text-indigo-700 bg-indigo-100 px-2 py-1 rounded-md';
    }
    
    // Educational content
    if (lowerContent.includes('here\'s what i can tell you') || lowerContent.includes('about') ||
        lowerContent.includes('هذا ما يمكنني') || lowerContent.includes('esto es lo que')) {
      return 'font-bold text-blue-700 bg-blue-100 px-2 py-1 rounded-md';
    }
    
    // Processing states
    if (lowerContent.includes('processing') || lowerContent.includes('upload') ||
        lowerContent.includes('معالجة') || lowerContent.includes('procesando')) {
      return 'font-bold text-orange-700 bg-orange-100 px-2 py-1 rounded-md';
    }
    
    // Error messages
    if (lowerContent.includes('sorry') || lowerContent.includes('error') ||
        lowerContent.includes('آسف') || lowerContent.includes('خطأ') || lowerContent.includes('lo siento')) {
      return 'font-bold text-red-700 bg-red-100 px-2 py-1 rounded-md';
    }
    
    // Positive messages
    if (lowerContent.includes('thanks') || lowerContent.includes('help') ||
        lowerContent.includes('شكرا') || lowerContent.includes('مساعدة') || lowerContent.includes('gracias')) {
      return 'font-bold text-green-700 bg-green-100 px-2 py-1 rounded-md';
    }
    
    // Default bold styling for all languages
    return 'font-bold text-gray-800';
  };

  // Function to get icon based on message content (works for all languages)
  const getMessageIcon = (text) => {
    if (!text) return null;
    
    const lowerText = text.toLowerCase();
    
    // Grade and performance (multilingual detection)
    if (lowerText.includes('grade') || lowerText.includes('performance') || 
        lowerText.includes('درجة') || lowerText.includes('الأداء') ||
        lowerText.includes('calificación') || lowerText.includes('rendimiento') ||
        text.includes('/100') || text.includes('%')) {
      return <Award className="w-4 h-4 text-purple-600" />;
    }
    
    // Educational explanations
    if (lowerText.includes('tell you about') || lowerText.includes('here\'s what') ||
        lowerText.includes('هذا ما يمكنني') || lowerText.includes('esto es lo que') ||
        lowerText.includes('explanation') || lowerText.includes('شرح')) {
      return <BookOpen className="w-4 h-4 text-blue-600" />;
    }
    
    // Translation indicators
    if (lowerText.includes('translated from') || lowerText.includes('مترجم من') ||
        lowerText.includes('traducido de')) {
      return <Globe className="w-4 h-4 text-indigo-600" />;
    }
    
    // Processing and file operations
    if (lowerText.includes('processing') || lowerText.includes('upload') ||
        lowerText.includes('معالجة') || lowerText.includes('رفع') ||
        lowerText.includes('procesando') || lowerText.includes('subir')) {
      return <FileText className="w-4 h-4 text-orange-600" />;
    }
    
    // Positive interactions
    if (lowerText.includes('thanks') || lowerText.includes('help') ||
        lowerText.includes('شكرا') || lowerText.includes('مساعدة') ||
        lowerText.includes('gracias') || lowerText.includes('ayuda')) {
      return <MessageCircle className="w-4 h-4 text-green-600" />;
    }
    
    // Errors and problems
    if (lowerText.includes('sorry') || lowerText.includes('error') ||
        lowerText.includes('آسف') || lowerText.includes('خطأ') ||
        lowerText.includes('lo siento') || lowerText.includes('error')) {
      return <XCircle className="w-4 h-4 text-red-600" />;
    }
    
    return null;
  };

  // Hide technical confidence metrics from users
  const shouldShowTechnicalDetails = false;
  
  // Clean text by removing only technical details, preserve all other formatting
  const cleanText = (text) => {
    if (!text) return '';
    
    // Only remove technical confidence details (keep all other formatting)
    let cleanedText = text
      .replace(/\(confidence:\s*\d+(?:\.\d+)?%\)/gi, '')
      .replace(/\(low confidence:\s*\d+(?:\.\d+)?%\)/gi, '')
      .replace(/\(detected intent with \d+(?:\.\d+)?% confidence\)/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    // Keep ALL formatting including **bold**, emojis, etc. for both English and non-English
    // The API will handle language-appropriate content, UI just displays it properly
    
    return cleanedText;
  };

  // Main render for user messages (simple formatting)
  if (isUser) {
    return (
      <div className="text-sm leading-relaxed text-white">
        {formatText(message.text)}
      </div>
    );
  }

  // Enhanced render for bot messages with multilingual support
  const cleanedText = cleanText(message.text);
  const messageIcon = getMessageIcon(cleanedText);
  
  // Detect text direction for proper RTL support
  const hasArabicText = /[\u0600-\u06FF]/.test(cleanedText);
  const textDirection = hasArabicText ? 'rtl' : 'ltr';

  return (
    <div className="space-y-3" dir={textDirection}>
      {/* Message header with icon and language-appropriate spacing */}
      {messageIcon && (
        <div className={`flex items-center space-x-2 mb-2 ${hasArabicText ? 'justify-end' : 'justify-start'}`}>
          {messageIcon}
          <span className="text-xs font-medium text-gray-600">EdRoom AI</span>
        </div>
      )}
      
      {/* Formatted message content with proper text direction */}
      <div className={`space-y-2 ${hasArabicText ? 'text-right' : 'text-left'}`}>
        {formatText(cleanedText)}
      </div>
      
      {/* Learn More section removed */}
    </div>
  );
};

export default MessageFormatter;
