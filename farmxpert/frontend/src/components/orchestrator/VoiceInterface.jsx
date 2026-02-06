import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

const VoiceContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1rem 0;
`;

const VoiceControls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
`;

const VoiceButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  transition: all 0.2s ease;
  
  ${props => {
    if (props.isRecording) {
      return `
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        animation: pulse 1.5s infinite;
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `;
    } else if (props.isPlaying) {
      return `
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
      `;
    } else {
      return `
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      `;
    }
  }}
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const VoiceStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
`;

const StatusIndicator = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'recording': return '#ef4444';
      case 'playing': return '#10b981';
      case 'idle': return '#9ca3af';
      default: return '#9ca3af';
    }
  }};
  animation: ${props => props.status === 'recording' ? 'pulse 1s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const VoiceInput = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  transition: all 0.2s ease;
  
  ${props => props.isRecording && `
    border-color: #ef4444;
    background: #fef2f2;
  `}
`;

const VoiceText = styled.div`
  flex: 1;
  font-size: 0.875rem;
  color: #374151;
  min-height: 20px;
  
  ${props => props.isRecording && `
    color: #dc2626;
    font-weight: 500;
  `}
`;

const LanguageSelector = styled.select`
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const VoiceInterface = ({ 
  onVoiceInput = null,
  onVoiceOutput = null,
  textToSpeak = '',
  supportedLanguages = ['en', 'hi'],
  defaultLanguage = 'en',
  autoRestartRecognition = false,
  className = '' 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [language, setLanguage] = useState(defaultLanguage);
  const [recognition, setRecognition] = useState(null);
  const [speechSynthesis, setSpeechSynthesis] = useState(null);
  
  const recognitionRef = useRef(null);
  const speechRef = useRef(null);
  const transcriptRef = useRef('');

  useEffect(() => {
    // Initialize Speech Recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = language === 'hi' ? 'hi-IN' : 'en-US';
      
      recognitionInstance.onstart = () => {
        setIsRecording(true);
        setTranscript('');
      };
      
      recognitionInstance.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const combinedTranscript = (finalTranscript + interimTranscript).trimStart();
        transcriptRef.current = combinedTranscript;
        setTranscript(combinedTranscript);
      };
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };
      
      recognitionInstance.onend = () => {
        setIsRecording(false);
        const finalText = (transcriptRef.current || '').trim();
        if (finalText && onVoiceInput) {
          onVoiceInput(finalText);
        }

        transcriptRef.current = '';
        setTranscript('');

        if (autoRestartRecognition) {
          try {
            recognitionInstance.start();
          } catch (error) {
            // Ignore if start is called while already started.
          }
        }
      };
      
      setRecognition(recognitionInstance);
      recognitionRef.current = recognitionInstance;
    }
    
    // Initialize Speech Synthesis
    if ('speechSynthesis' in window) {
      setSpeechSynthesis(window.speechSynthesis);
      speechRef.current = window.speechSynthesis;
    }

    return () => {
      try {
        recognitionRef.current?.stop();
      } catch (error) {
        // no-op
      }

      try {
        speechRef.current?.cancel();
      } catch (error) {
        // no-op
      }
    };
  }, [language, onVoiceInput, autoRestartRecognition]);

  const startRecording = () => {
    if (recognition && !isRecording) {
      try {
        recognition.start();
      } catch (error) {
        console.error('Failed to start recording:', error);
      }
    }
  };

  const stopRecording = () => {
    if (recognition && isRecording) {
      try {
        recognition.stop();
      } catch (error) {
        console.error('Failed to stop recording:', error);
      }
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const speakText = (text) => {
    if (speechSynthesis && text) {
      // Stop any current speech
      speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === 'hi' ? 'hi-IN' : 'en-US';
      utterance.rate = 0.9;
      utterance.pitch = 1;
      
      utterance.onstart = () => setIsPlaying(true);
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);
      
      speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if (speechSynthesis) {
      speechSynthesis.cancel();
      setIsPlaying(false);
    }
  };

  const toggleSpeaking = () => {
    if (isPlaying) {
      stopSpeaking();
    } else if (textToSpeak) {
      speakText(textToSpeak);
    }
  };

  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    if (recognition) {
      recognition.lang = newLanguage === 'hi' ? 'hi-IN' : 'en-US';
    }
  };

  const getStatusText = () => {
    if (isRecording) return 'Recording...';
    if (isPlaying) return 'Speaking...';
    return 'Ready';
  };

  const getStatus = () => {
    if (isRecording) return 'recording';
    if (isPlaying) return 'playing';
    return 'idle';
  };

  const languageNames = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)'
  };

  return (
    <VoiceContainer className={className}>
      <VoiceControls>
        <VoiceButton
          onClick={toggleRecording}
          isRecording={isRecording}
          disabled={!recognition}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title={isRecording ? 'Stop Recording' : 'Start Recording'}
        >
          {isRecording ? '⏹️' : '🎤'}
        </VoiceButton>
        
        <VoiceButton
          onClick={toggleSpeaking}
          isPlaying={isPlaying}
          disabled={!speechSynthesis || !textToSpeak}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title={isPlaying ? 'Stop Speaking' : 'Speak Response'}
        >
          {isPlaying ? '⏹️' : '🔊'}
        </VoiceButton>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <VoiceStatus>
            <StatusIndicator status={getStatus()} />
            {getStatusText()}
          </VoiceStatus>
          
          <LanguageSelector
            value={language}
            onChange={(e) => handleLanguageChange(e.target.value)}
          >
            {supportedLanguages.map(lang => (
              <option key={lang} value={lang}>
                {languageNames[lang] || lang}
              </option>
            ))}
          </LanguageSelector>
        </div>
      </VoiceControls>
      
      <AnimatePresence>
        {(isRecording || transcript) && (
          <VoiceInput
            isRecording={isRecording}
            as={motion.div}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span style={{ fontSize: '1.25rem' }}>
              {isRecording ? '🎤' : '📝'}
            </span>
            <VoiceText isRecording={isRecording}>
              {transcript || (isRecording ? 'Listening...' : '')}
            </VoiceText>
          </VoiceInput>
        )}
      </AnimatePresence>
      
      {!recognition && (
        <div style={{ 
          color: '#ef4444', 
          fontSize: '0.875rem', 
          textAlign: 'center',
          padding: '1rem',
          background: '#fef2f2',
          borderRadius: '8px',
          border: '1px solid #fecaca'
        }}>
          ⚠️ Speech recognition is not supported in this browser
        </div>
      )}
      
      {!speechSynthesis && (
        <div style={{ 
          color: '#f59e0b', 
          fontSize: '0.875rem', 
          textAlign: 'center',
          padding: '1rem',
          background: '#fffbeb',
          borderRadius: '8px',
          border: '1px solid #fed7aa'
        }}>
          ⚠️ Speech synthesis is not supported in this browser
        </div>
      )}
    </VoiceContainer>
  );
};

export default VoiceInterface;
