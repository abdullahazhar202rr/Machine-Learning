import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Mic, MicOff, Volume2, VolumeX, Send, Bot, Phone, PhoneOff, 
  Camera, Upload, Image, FileText, Paperclip, X, Play, Pause,
  Loader2, Eye, Download
} from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: FileAttachment[];
}

interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  preview?: string;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [continuousMode, setContinuousMode] = useState(false);
  const [isCallMode, setIsCallMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState({
    rate: 0.9,
    pitch: 1.1,
    volume: 0.8,
    voiceIndex: 0
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    // Initialize speech recognition
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript + interimTranscript);

        if (finalTranscript) {
          setInputText(finalTranscript);
          if (continuousMode || isCallMode) {
            handleSendMessage(finalTranscript);
          }
        }
      };

      recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        setError(`Speech recognition error: ${event.error}`);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        setTranscript('');
        
        // Auto-restart in call mode
        if (isCallMode && !isSpeaking) {
          setTimeout(() => startListening(), 500);
        }
      };
    }

    // Initialize speech synthesis
    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [continuousMode, isCallMode, isSpeaking]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Handle call mode
    if (isCallMode) {
      startListening();
    } else {
      stopListening();
    }
  }, [isCallMode]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setError(null);
      setTranscript('');
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const getOptimalVoice = () => {
    if (!synthRef.current) return null;
    
    const voices = synthRef.current.getVoices();
    
    // Prioritize high-quality voices
    const preferredVoices = [
      // Premium/Neural voices
      voices.find(v => v.name.includes('Neural') && v.lang.startsWith('en')),
      voices.find(v => v.name.includes('Enhanced') && v.lang.startsWith('en')),
      voices.find(v => v.name.includes('Premium') && v.lang.startsWith('en')),
      // Platform-specific quality voices
      voices.find(v => v.name.includes('Samantha')), // macOS
      voices.find(v => v.name.includes('Zira') && v.lang.startsWith('en')), // Windows
      voices.find(v => v.name.includes('Google') && v.lang.startsWith('en')), // Chrome
      // Fallback to any English voice
      voices.find(v => v.lang.startsWith('en-US')),
      voices.find(v => v.lang.startsWith('en'))
    ];

    return preferredVoices.find(v => v) || voices[voiceSettings.voiceIndex] || null;
  };

  const speak = (text: string) => {
    if (synthRef.current && voiceEnabled) {
      // Stop any ongoing speech
      synthRef.current.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = voiceSettings.rate;
      utterance.pitch = voiceSettings.pitch;
      utterance.volume = voiceSettings.volume;
      
      const voice = getOptimalVoice();
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        // In call mode, restart listening after speaking
        if (isCallMode) {
          setTimeout(() => startListening(), 300);
        }
      };
      utterance.onerror = () => setIsSpeaking(false);

      synthRef.current.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleCallMode = () => {
    setIsCallMode(!isCallMode);
    if (!isCallMode) {
      // Starting call mode
      setVoiceEnabled(true);
      setContinuousMode(true);
    }
  };

  const handleFileUpload = (files: FileList) => {
    Array.from(files).forEach(file => {
      const attachment: FileAttachment = {
        id: Date.now().toString() + Math.random(),
        name: file.name,
        type: file.type,
        size: file.size,
        url: URL.createObjectURL(file)
      };

      // Generate preview for images
      if (file.type.startsWith('image/')) {
        attachment.preview = attachment.url;
      }

      setAttachments(prev => [...prev, attachment]);
    });
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => {
      const attachment = prev.find(a => a.id === id);
      if (attachment) {
        URL.revokeObjectURL(attachment.url);
      }
      return prev.filter(a => a.id !== id);
    });
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 }, 
        audio: false 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setShowCamera(true);
    } catch (error) {
      setError('Camera access denied or not available');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        
        canvas.toBlob(blob => {
          if (blob) {
            const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' });
            const attachment: FileAttachment = {
              id: Date.now().toString(),
              name: file.name,
              type: file.type,
              size: file.size,
              url: URL.createObjectURL(file),
              preview: URL.createObjectURL(file)
            };
            setAttachments(prev => [...prev, attachment]);
          }
        }, 'image/jpeg', 0.8);
      }
    }
    closeCamera();
  };

  const closeCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
  };

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputText.trim();
    if (!text && attachments.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString() + '-user',
      type: 'user',
      content: text || 'Sent attachments',
      timestamp: new Date(),
      attachments: [...attachments]
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setAttachments([]);
    setIsLoading(true);
    setError(null);

    try {
      // Prepare message content with attachments info
      let messageContent = text;
      if (attachments.length > 0) {
        const attachmentInfo = attachments.map(att => 
          `[Attachment: ${att.name} (${att.type})]`
        ).join(' ');
        messageContent = text ? `${text}\n\n${attachmentInfo}` : attachmentInfo;
      }

      const response = await fetch('http://127.0.0.1:8080/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_tokens: 200,
          messages: [{ role: 'user', content: messageContent }]
        })
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      const assistantResponse = data.choices[0].message.content;

      const assistantMessage: Message = {
        id: Date.now().toString() + '-assistant',
        type: 'assistant',
        content: assistantResponse,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Speak the response
      if (voiceEnabled) {
        speak(assistantResponse);
      }

    } catch (error) {
      const errorMessage = `Failed to get response: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setError(errorMessage);
      
      const errorResponse: Message = {
        id: Date.now().toString() + '-error',
        type: 'assistant',
        content: "I apologize, but I'm having trouble connecting to the server. Please check your connection and try again.",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      handleFileUpload(e.dataTransfer.files);
    }
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (type.includes('pdf') || type.includes('document')) return <FileText className="w-4 h-4" />;
    return <Paperclip className="w-4 h-4" />;
  };

  return (
    <div 
      className={`min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col ${
        isDragOver ? 'bg-blue-900/20' : ''
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-lg border-b border-slate-700 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center ${
              isCallMode ? 'animate-pulse ring-4 ring-green-500/50' : ''
            }`}>
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Jarvis AI Assistant</h1>
              <p className="text-sm text-slate-400">
                {isCallMode ? 'Voice Call Active' : 'Advanced AI Chat'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Call Mode Toggle */}
            <button
              onClick={toggleCallMode}
              className={`p-3 rounded-full transition-all ${
                isCallMode 
                  ? 'bg-green-500 text-white shadow-lg shadow-green-500/25 animate-pulse' 
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
              }`}
              title={isCallMode ? 'End voice call' : 'Start voice call'}
            >
              {isCallMode ? <PhoneOff className="w-5 h-5" /> : <Phone className="w-5 h-5" />}
            </button>

            <button
              onClick={() => setContinuousMode(!continuousMode)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                continuousMode 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                  : 'bg-slate-700 text-slate-400 border border-slate-600'
              }`}
            >
              {continuousMode ? 'Continuous' : 'Manual'}
            </button>
            
            <button
              onClick={() => setVoiceEnabled(!voiceEnabled)}
              className={`p-2 rounded-full transition-all ${
                voiceEnabled 
                  ? 'bg-blue-500/20 text-blue-400' 
                  : 'bg-slate-700 text-slate-500'
              }`}
              title={voiceEnabled ? 'Disable voice responses' : 'Enable voice responses'}
            >
              {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden flex flex-col max-w-4xl mx-auto w-full ">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Welcome to Enhanced Jarvis</h3>
              <p className="text-slate-400 mb-4">Voice calls • File uploads • Camera capture</p>
              
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-lg ${
                  message.type === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                    : 'bg-slate-800/80 backdrop-blur-sm text-slate-100 border border-slate-700'
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
                
                {/* Attachments */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {message.attachments.map((attachment) => (
                      <div key={attachment.id} className="flex items-center gap-2 p-2 bg-black/20 rounded-lg">
                        {attachment.preview ? (
                          <img 
                            src={attachment.preview} 
                            alt={attachment.name}
                            className="w-12 h-12 object-cover rounded"
                          />
                        ) : (
                          <div className="w-12 h-12 bg-slate-600 rounded flex items-center justify-center">
                            {getFileIcon(attachment.type)}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">{attachment.name}</p>
                          <p className="text-xs opacity-70">{formatFileSize(attachment.size)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <p className={`text-xs mt-2 ${
                  message.type === 'user' ? 'text-blue-100' : 'text-slate-400'
                }`}>
                  {formatTime(message.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start animate-in slide-in-from-bottom-2">
              <div className="bg-slate-800/80 backdrop-blur-sm border border-slate-700 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  <span className="text-slate-400 text-sm">Jarvis is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-4 mb-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Voice Transcript */}
        {transcript && (
          <div className="mx-4 mb-2 p-3 bg-blue-500/20 border border-blue-500/50 rounded-lg">
            <p className="text-blue-400 text-sm">
              {isCallMode ? '🎙️ Call Mode: ' : 'Listening: '}
              <span className="text-white">{transcript}</span>
            </p>
          </div>
        )}

        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="mx-4 mb-2 p-3 bg-slate-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Paperclip className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-400">Attachments ({attachments.length})</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {attachments.map((attachment) => (
                <div key={attachment.id} className="relative group">
                  {attachment.preview ? (
                    <img 
                      src={attachment.preview} 
                      alt={attachment.name}
                      className="w-16 h-16 object-cover rounded border border-slate-600"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-slate-700 rounded border border-slate-600 flex items-center justify-center">
                      {getFileIcon(attachment.type)}
                    </div>
                  )}
                  <button
                    onClick={() => removeAttachment(attachment.id)}
                    className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 bg-slate-800/50 backdrop-blur-lg border-t border-slate-700   rounded-3xl mb-4 ">
          <div className="flex items-end gap-3">
            {/* File Upload Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-3 bg-slate-700 text-slate-400 rounded-full hover:bg-slate-600 hover:text-white transition-all"
              title="Upload files"
            >
              <Upload className="w-5 h-5" />
            </button>

            {/* Camera Button */}
            <button
              onClick={startCamera}
              className="p-3 bg-slate-700 text-slate-400 rounded-full hover:bg-slate-600 hover:text-white transition-all"
              title="Take photo"
            >
              <Camera className="w-5 h-5" />
            </button>

            {/* Voice Button */}
            <button
              onMouseDown={startListening}
              onMouseUp={stopListening}
              onTouchStart={startListening}
              onTouchEnd={stopListening}
              disabled={!recognitionRef.current || isCallMode}
              className={`p-3 rounded-full transition-all duration-200 ${
                isListening
                  ? 'bg-red-500 text-white shadow-lg shadow-red-500/25 animate-pulse'
                  : isCallMode
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
              } ${!recognitionRef.current ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={
                isCallMode 
                  ? 'Call mode active' 
                  : isListening 
                  ? 'Release to stop listening' 
                  : 'Hold to speak'
              }
            >
              {isCallMode ? <Phone className="w-5 h-5" /> : isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isCallMode ? "Voice call active..." : "Type your message or use voice..."}
                disabled={isCallMode}
                className="w-full bg-slate-700 text-white overflow-hidden placeholder-slate-400 border border-slate-600 rounded-2xl px-4 py-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-50"
                rows={1}
                style={{ maxHeight: '120px' }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = target.scrollHeight + 'px';
                }}
              />
              
              {/* Send Button */}
              <button
                onClick={() => handleSendMessage()}
                disabled={(!inputText.trim() && attachments.length === 0) || isLoading || isCallMode}
                className="absolute right-2 bottom-2 p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            {/* Stop Speaking Button */}
            {isSpeaking && (
              <button
                onClick={stopSpeaking}
                className="p-3 bg-orange-500 text-white rounded-full hover:bg-orange-600 transition-all animate-pulse"
                title="Stop speaking"
              >
                <VolumeX className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="mt-2 text-xs text-slate-500 text-center">
            {isCallMode ? (
              <span className="text-green-400">🎙️ Voice call active - Speak naturally</span>
            ) : recognitionRef.current ? (
              continuousMode ? 
                "Hold microphone to speak • Continuous mode enabled" : 
                "Hold microphone to speak • Press Enter to send"
            ) : (
              "Voice recognition not supported in this browser"
            )}
          </div>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.json"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        className="hidden"
      />

      {/* Camera Modal */}
      {showCamera && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 rounded-2xl p-6 max-w-lg w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Camera</h3>
              <button
                onClick={closeCamera}
                className="p-2 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="relative mb-4">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full rounded-lg bg-slate-900"
              />
              <canvas ref={canvasRef} className="hidden" />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={capturePhoto}
                className="flex-1 bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
              >
                📸 Capture Photo
              </button>
              <button
                onClick={closeCamera}
                className="px-6 bg-slate-700 text-slate-300 py-3 rounded-lg hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Drag & Drop Overlay */}
      {isDragOver && (
        <div className="fixed inset-0 bg-blue-500/20 backdrop-blur-sm z-40 flex items-center justify-center">
          <div className="bg-slate-800 rounded-2xl p-8 text-center border-2 border-dashed border-blue-500">
            <Upload className="w-12 h-12 text-blue-400 mx-auto mb-4" />
            <p className="text-white text-lg font-semibold">Drop files here</p>
            <p className="text-slate-400">Images, documents, and more</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;