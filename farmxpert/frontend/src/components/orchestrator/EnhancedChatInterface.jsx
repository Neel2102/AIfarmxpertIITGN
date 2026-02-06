import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { useOrchestrator } from '../../contexts/OrchestratorContext';

// Import orchestrator components
import AgentActivationChips from './AgentActivationChips';
import ReasoningTree from './ReasoningTree';
import WorkflowVisualizer from './WorkflowVisualizer';
import VoiceInterface from './VoiceInterface';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  font-family: 'Inter', sans-serif;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
`;

const HeaderTitle = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const HeaderStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => props.isConnected ? '#10b981' : '#ef4444'};
  animation: ${props => props.isConnected ? 'pulse 2s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const ChatContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const Message = styled(motion.div)`
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  max-width: 80%;
  
  ${props => props.isUser ? `
    align-self: flex-end;
    flex-direction: row-reverse;
  ` : `
    align-self: flex-start;
  `}
`;

const MessageAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
  
  ${props => props.isUser ? `
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
  ` : `
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
  `}
`;

const MessageContent = styled.div`
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 18px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  max-width: 100%;
  
  ${props => props.isUser ? `
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    border-color: #3b82f6;
  ` : `
    background: white;
    color: #1f2937;
  `}
`;

const MessageText = styled.div`
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
`;

const MessageTime = styled.div`
  font-size: 0.75rem;
  color: ${props => props.isUser ? 'rgba(255, 255, 255, 0.7)' : '#9ca3af'};
  margin-top: 0.5rem;
  text-align: ${props => props.isUser ? 'right' : 'left'};
`;

const WorkflowSection = styled(motion.div)`
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
`;

const InputSection = styled.div`
  padding: 1rem 2rem;
  background: white;
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.1);
`;

const InputContainer = styled.div`
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  max-width: 800px;
  margin: 0 auto;
`;

const TextInput = styled.textarea`
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 0.875rem;
  font-family: inherit;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  &::placeholder {
    color: #9ca3af;
  }
`;

const SendButton = styled(motion.button)`
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const LoadingIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
`;

const TypingDots = styled.div`
  display: flex;
  gap: 0.25rem;
  
  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #9ca3af;
    animation: typing 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
  
  @keyframes typing {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

const EnhancedChatInterface = ({ className = '' }) => {
  const {
    loading: isProcessing,
    error,
    session,
    currentWorkflow: workflow,
    messages,
    processQuery,
    submitVoiceInput,
    clearError
  } = useOrchestrator();
  
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(true);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [inputText]);

  const handleSendMessage = async () => {
    if (inputText.trim() && !isProcessing) {
      try {
        await processQuery(inputText.trim(), session?.id);
        setInputText('');
      } catch (error) {
        console.error('Failed to process query:', error);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleVoiceInput = async (audioBlob) => {
    try {
      await submitVoiceInput(audioBlob, session?.id);
    } catch (error) {
      console.error('Failed to process voice input:', error);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getActiveAgents = () => {
    if (!workflow || !workflow.tasks) return [];
    
    return workflow.tasks
      .filter(task => task.status === 'running' || task.status === 'completed')
      .map(task => ({
        id: task.id,
        name: task.agent_name,
        status: task.status
      }));
  };

  const getAgentOutputs = () => {
    if (!workflow || !workflow.tasks) return [];
    
    return workflow.tasks
      .filter(task => task.status === 'completed' && task.outputs)
      .map(task => ({
        id: task.id,
        name: task.agent_name,
        status: task.status,
        outputs: task.outputs,
        execution_time: task.execution_time
      }));
  };

  const getCurrentResponse = () => {
    const lastMessage = messages[messages.length - 1];
    return lastMessage && lastMessage.type === 'system' ? lastMessage.content : '';
  };

  return (
    <ChatContainer className={className}>
      <ChatHeader>
        <HeaderTitle>
          🤖 FarmXpert AI Assistant
        </HeaderTitle>
        
        <HeaderStatus>
          <StatusDot isConnected={isConnected} />
          {isConnected ? 'Connected' : 'Disconnected'}
          {session?.id && (
            <span style={{ marginLeft: '1rem', fontSize: '0.75rem' }}>
              Session: {session.id.slice(-8)}
            </span>
          )}
        </HeaderStatus>
      </ChatHeader>

      <ChatContent>
        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              style={{
                background: '#fee2e2',
                border: '1px solid #fecaca',
                color: '#dc2626',
                padding: '1rem',
                margin: '1rem 2rem',
                borderRadius: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <span>❌ {error}</span>
              <button
                onClick={clearError}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#dc2626',
                  cursor: 'pointer',
                  fontSize: '1.2rem'
                }}
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <MessagesContainer>
          <AnimatePresence>
            {messages.map((message, index) => (
              <Message
                key={message.id || index}
                isUser={message.type === 'user'}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <MessageAvatar isUser={message.type === 'user'}>
                  {message.type === 'user' ? '👤' : '🤖'}
                </MessageAvatar>
                
                <MessageContent isUser={message.type === 'user'}>
                  <MessageText>{message.content}</MessageText>
                  <MessageTime isUser={message.type === 'user'}>
                    {formatTime(message.timestamp)}
                  </MessageTime>
                </MessageContent>
              </Message>
            ))}
          </AnimatePresence>

          {isProcessing && (
            <Message isUser={false}>
              <MessageAvatar isUser={false}>🤖</MessageAvatar>
              <MessageContent isUser={false}>
                <LoadingIndicator>
                  <span>Processing your request...</span>
                  <TypingDots>
                    <span></span>
                    <span></span>
                    <span></span>
                  </TypingDots>
                </LoadingIndicator>
              </MessageContent>
            </Message>
          )}

          <div ref={messagesEndRef} />
        </MessagesContainer>

        {/* Agent Activation Chips */}
        <AnimatePresence>
          {workflow && workflow.tasks && (
            <WorkflowSection
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <AgentActivationChips
                agents={getActiveAgents()}
                showStatus={true}
              />
            </WorkflowSection>
          )}
        </AnimatePresence>

        {/* Workflow Visualizer */}
        <AnimatePresence>
          {workflow && (
            <WorkflowSection
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <WorkflowVisualizer
                workflow={workflow}
                isActive={isProcessing}
              />
            </WorkflowSection>
          )}
        </AnimatePresence>

        {/* Reasoning Tree */}
        <AnimatePresence>
          {workflow && !isProcessing && (
            <WorkflowSection
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ReasoningTree
                data={getAgentOutputs()}
                defaultExpanded={false}
              />
            </WorkflowSection>
          )}
        </AnimatePresence>
      </ChatContent>

      <InputSection>
        <InputContainer>
          <TextInput
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about crop planning, pest diagnosis, yield optimization, or any farming advice..."
            disabled={isProcessing}
          />
          
          <SendButton
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isProcessing}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isProcessing ? (
              <>
                <span>⏳</span>
                Processing...
              </>
            ) : (
              <>
                <span>📤</span>
                Send
              </>
            )}
          </SendButton>
        </InputContainer>

        {/* Voice Interface */}
        <VoiceInterface
          onVoiceInput={handleVoiceInput}
          textToSpeak={getCurrentResponse()}
          supportedLanguages={['en', 'hi']}
          defaultLanguage="en"
        />
      </InputSection>
    </ChatContainer>
  );
};

export default EnhancedChatInterface;
