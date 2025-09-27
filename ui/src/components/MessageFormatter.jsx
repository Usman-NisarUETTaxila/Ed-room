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
  // Function to parse and format text with markdown-like syntax
  const formatText = (text) => {
    if (!text) return '';
    
    // Split text by double newlines to create sections
    const sections = text.split('\n\n');
    
    return sections.map((section, sectionIndex) => {
      // Split each section by single newlines
      const lines = section.split('\n');
      
      return (
        <div key={sectionIndex} className={sectionIndex > 0 ? 'mt-4' : ''}>
          {lines.map((line, lineIndex) => {
            // Skip empty lines
            if (!line.trim()) return null;
            
            // Check if line starts with separator (===)
            if (line.trim().startsWith('===')) {
              return (
                <div key={lineIndex} className="my-4 border-t border-gray-200"></div>
              );
            }
            
            return (
              <div key={lineIndex} className={lineIndex > 0 ? 'mt-2' : ''}>
                {formatLine(line)}
              </div>
            );
          })}
        </div>
      );
    });
  };

  // Function to format individual lines with bold, emojis, and special formatting
  const formatLine = (line) => {
    // Handle different types of lines
    if (line.includes('**') || line.includes('*')) {
      return formatWithMarkdown(line);
    }
    
    return <span className="text-sm leading-relaxed">{line}</span>;
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
      
      {/* Enhanced explanation display with multilingual support */}
      {message.explanation_result && (
        <div className={`mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg ${hasArabicText ? 'text-right' : 'text-left'}`} dir={textDirection}>
          <div className={`flex items-center space-x-2 mb-3 ${hasArabicText ? 'justify-end space-x-reverse' : 'justify-start'}`}>
            <BookOpen className="w-5 h-5 text-blue-600" />
            <span className="text-base font-medium text-blue-800">
              {hasArabicText ? 'تعلم المزيد' : 'Learn More'}
            </span>
          </div>
          <div className="text-sm text-blue-700 leading-relaxed" dir={textDirection}>
            {message.explanation_result.explanation}
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageFormatter;
