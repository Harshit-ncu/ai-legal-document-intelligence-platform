import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { sendChatMessage } from '../services/geminiService';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Spinner } from '../components/ui/Spinner';
import { User, Scale, Bot, UploadCloud } from 'lucide-react';
import styles from './ChatPage.module.css';

// ── Helpers ───────────────────────────────────────────────

function resolveError(err) {
  const status = err.response?.status;
  if (status === 400 || status === 422) return 'Invalid request. Please rephrase your question.';
  if (status === 404) return 'AI Service endpoint not found.';
  if (status === 429) return 'Rate limit exceeded. Please wait a moment and try again.';
  if (status >= 500) return 'AI Service is currently unavailable.';
  if (err.request) return 'Network error. Please check your connection.';
  return 'Failed to get a response. Please try again.';
}

// ── Sub-components ────────────────────────────────────────

function UserBubble({ text }) {
  return (
    <div className={`${styles.messageRow} ${styles.user}`}>
      <div className={styles.avatar}>
        <User size={18} />
      </div>
      <div className={styles.bubble}>{text}</div>
    </div>
  );
}

function AiBubble({ data, onFollowUp }) {
  return (
    <div className={`${styles.messageRow} ${styles.ai}`}>
      <div className={styles.avatar}>
        <Bot size={18} />
      </div>
      <div>
        <div className={styles.bubble}>
          <p className={styles.answerText}>{data.answer}</p>
          {data.confidence != null && (
            <span className={styles.confidenceLabel}>
              Confidence: {data.confidence}/100
            </span>
          )}

          {/* Expandable extras */}
          {(data.sourceReferences?.length > 0 ||
            data.reasoning ||
            data.limitations?.length > 0) && (
            <div className={styles.aiExtras}>

              {data.reasoning && (
                <div className={styles.extraSection}>
                  <strong>Reasoning</strong>
                  {data.reasoning}
                </div>
              )}

              {data.sourceReferences?.length > 0 && (
                <div className={styles.extraSection}>
                  <strong>Source References</strong>
                  {data.sourceReferences.map((ref, i) => (
                    <div key={i} className={styles.sourceRef}>
                      <div className={styles.sourceRefTitle}>
                        {ref.section} — {ref.clause}
                      </div>
                      {ref.excerpt && (
                        <div className={styles.sourceRefExcerpt}>"{ref.excerpt}"</div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {data.limitations?.length > 0 && (
                <div className={styles.extraSection}>
                  <strong>Limitations</strong>
                  <ul className={styles.extraList}>
                    {data.limitations.map((lim, i) => <li key={i}>{lim}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Follow-up question chips */}
        {data.followUpQuestions?.length > 0 && (
          <div className={styles.followUps}>
            {data.followUpQuestions.map((q, i) => (
              <button
                key={i}
                className={styles.followUpChip}
                onClick={() => onFollowUp(q)}
                title={q}
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ThinkingBubble() {
  return (
    <div className={styles.thinkingRow}>
      <div className={styles.avatar}>
        <Bot size={18} />
      </div>
      <div className={styles.thinkingBubble}>
        <Spinner size="small" /> Thinking…
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────

const ChatPage = () => {
  const navigate = useNavigate();
  const { state } = useDocumentContext();
  const { extractedText, documentType } = state;

  // Local-only chat state — DocumentContext is never modified
  const [messages, setMessages] = useState([]);   // { role: 'user'|'ai', text?, data? }
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState(null);

  const messageEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSend = useCallback(async (overrideText) => {
    const question = (overrideText ?? inputText).trim();
    if (!question || isThinking) return;

    setInputText('');
    setError(null);
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setIsThinking(true);

    try {
      const data = await sendChatMessage(extractedText, documentType, question);
      setMessages(prev => [...prev, { role: 'ai', data }]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(resolveError(err));
    } finally {
      setIsThinking(false);
      // Return focus to textarea after response
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [inputText, isThinking, extractedText, documentType]);

  const handleKeyDown = (e) => {
    // Enter sends; Shift+Enter inserts newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Empty guard ─────────────────────────────────────────
  if (!extractedText) {
    return (
      <div>
        <PageHeader
          title="AI Document Chat"
          description="Ask questions about the uploaded legal document."
        />
        <EmptyState
          icon={<UploadCloud size={48} />}
          title="No Document Uploaded"
          description="Upload a document before starting a conversation."
          action={
            <Button onClick={() => navigate('/upload')} variant="primary">
              Go to Upload
            </Button>
          }
        />
      </div>
    );
  }

  const canSend = inputText.trim().length > 0 && !isThinking;

  return (
    <div className={styles.container}>
      <PageHeader
        title="AI Document Chat"
        description="Ask questions about the uploaded legal document."
      />

      {error && (
        <ErrorMessage
          title="Chat Error"
          message={error}
          className={styles.errorBar}
        />
      )}

      {/* ── Chat window ── */}
      <div className={styles.chatCard}>

        {/* Message history */}
        <div className={styles.messageArea}>
          {messages.length === 0 && !isThinking && (
            <div className={styles.chatWelcome}>
              <div className={styles.chatWelcomeIcon}>
                <Scale size={48} />
              </div>
              <div className={styles.chatWelcomeTitle}>Ask anything about your document</div>
              <div className={styles.chatWelcomeBody}>
                Questions are answered strictly from the uploaded document's content — no guessing.
              </div>
            </div>
          )}

          {messages.map((msg, idx) =>
            msg.role === 'user'
              ? <UserBubble key={idx} text={msg.text} />
              : <AiBubble key={idx} data={msg.data} onFollowUp={(q) => handleSend(q)} />
          )}

          {isThinking && <ThinkingBubble />}

          {/* Scroll anchor */}
          <div ref={messageEndRef} />
        </div>

        {/* Input row */}
        <div className={styles.inputArea}>
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            rows={1}
            placeholder="Ask a question about the document… (Enter to send, Shift+Enter for newline)"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isThinking}
          />
          <Button
            onClick={() => handleSend()}
            disabled={!canSend}
            isLoading={isThinking}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
