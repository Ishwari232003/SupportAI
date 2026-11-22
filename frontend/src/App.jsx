
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activePage, setActivePage] = useState('assistant')

  const sendMessage = async (e) => {
    e.preventDefault()

    const userQuestion = question.trim()

    if (!userQuestion || loading) return

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userQuestion }
    ])

    setQuestion('')
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: userQuestion,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()

      setSessionId(data.session_id)

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || []
        }
      ])

    } catch (err) {
      setError(
        'Unable to connect to the support assistant. Please check that the backend is running.'
      )
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const newConversation = () => {
    setMessages([])
    setSessionId(null)
    setQuestion('')
    setError('')
  }

  return (
    <div className="app-container">

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">✦</div>
          <div>
            <h2>SupportAI</h2>
            <span>Customer Assistant</span>
          </div>
        </div>

        <button className="new-chat-btn" onClick={newConversation}>
          + New Conversation
        </button>

        <div className="sidebar-section">
          <p className="sidebar-label">WORKSPACE</p>

          <div
            className={`sidebar-item ${activePage === 'assistant' ? 'active' : ''}`}
            onClick={() => setActivePage('assistant')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                setActivePage('assistant')
              }
            }}
          >
            <span>💬</span> AI Assistant
          </div>

          <div
            className={`sidebar-item ${activePage === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActivePage('knowledge')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                setActivePage('knowledge')
              }
            }}
          >
            <span>📚</span> Knowledge Base
          </div>

        </div>

        <div className="sidebar-bottom">
          <div className="status-dot"></div>
          <span>Support Assistant Online</span>
        </div>

      </aside>

      <main className="main-content">

        {activePage === 'assistant' ? (

          <>
            <header className="topbar">
              <div>
                <h3>AI Customer Support</h3>
                <p>Intelligent assistance for your queries</p>
              </div>

              <div className="topbar-status">
                <span className="status-dot"></span>
                Online
              </div>
            </header>

            <section className="chat-area">

              {messages.length === 0 ? (

                <div className="welcome-screen">
                  <div className="welcome-icon">✦</div>

                  <h1>How can I help you today?</h1>

                  <p>
                    Ask me anything about products, warranties,
                    returns, orders and customer support policies.
                  </p>

                  <div className="suggestions">

                    <button onClick={() => setQuestion(
                      'What is the warranty period for Product X?'
                    )}>
                      <span>🛡️</span>
                      <div>
                        <strong>Warranty Information</strong>
                        <small>Check product warranty details</small>
                      </div>
                    </button>

                    <button onClick={() => setQuestion(
                      'What is the return policy?'
                    )}>
                      <span>↩️</span>
                      <div>
                        <strong>Return Policy</strong>
                        <small>Understand return eligibility</small>
                      </div>
                    </button>

                    <button onClick={() => setQuestion(
                      'How can I troubleshoot my product?'
                    )}>
                      <span>🔧</span>
                      <div>
                        <strong>Troubleshooting</strong>
                        <small>Get help with product issues</small>
                      </div>
                    </button>

                    <button onClick={() => setQuestion(
                      'How can I track my order?'
                    )}>
                      <span>📦</span>
                      <div>
                        <strong>Order Support</strong>
                        <small>Ask about order-related queries</small>
                      </div>
                    </button>

                  </div>
                </div>

              ) : (

                <div className="messages-container">

                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`message-row ${message.role}`}
                    >
                      <div className="message-avatar">
                        {message.role === 'user' ? 'U' : '✦'}
                      </div>

                      <div className="message-content">

                        <strong>
                          {message.role === 'user' ? 'You' : 'SupportAI'}
                        </strong>

                        <div className="message-bubble">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content.replace(/\\\|/g, '|')}
                          </ReactMarkdown>
                        </div>

                        {message.sources?.length > 0 && (
                          <div className="sources">
                            <strong>📚 Sources</strong>

                            {message.sources.map((source, i) => (
                              <div className="source-item" key={i}>
                                <span>📄</span>
                                <div>
                                  <strong>{source.document}</strong>
                                  <small>
                                    {source.section} · Page {source.page}
                                  </small>
                                </div>
                              </div>
                            ))}

                          </div>
                        )}

                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="message-row assistant">
                      <div className="message-avatar">✦</div>
                      <div className="message-content">
                        <strong>SupportAI</strong>
                        <div className="message-bubble typing">
                          Thinking...
                        </div>
                      </div>
                    </div>
                  )}

                </div>

              )}

              {error && <div className="error-message">{error}</div>}

            </section>

            <footer className="chat-footer">

              <form className="input-form" onSubmit={sendMessage}>

                <input
                  type="text"
                  placeholder="Ask your question here..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                />

                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                >
                  {loading ? '...' : '➤'}
                </button>

              </form>

              <p>
                SupportAI can make mistakes. Verify important information
                with the official policy documents.
              </p>

            </footer>
          </>

        ) : (

          <>

            <header className="topbar">
              <div>
                <h3>Knowledge Base</h3>
                <p>Manage your customer support knowledge documents</p>
              </div>
            </header>

            <section className="chat-area">

              <div className="welcome-screen">
                <div className="welcome-icon">📚</div>

                <h1>Knowledge Base</h1>

                <p>
                  Your company's knowledge base contains the documents
                  used by SupportAI to answer customer questions.
                </p>

                <div className="suggestions">
                  <div>
                    <span>📄</span>
                    <div>
                      <strong>Supported Documents</strong>
                      <small>PDF, DOCX, TXT, CSV and Excel</small>
                    </div>
                  </div>

                  <div>
                    <span>🔍</span>
                    <div>
                      <strong>Document Retrieval</strong>
                      <small>Search and retrieve relevant information</small>
                    </div>
                  </div>

                  <div>
                    <span>🧠</span>
                    <div>
                      <strong>AI-Powered Responses</strong>
                      <small>Answers grounded in knowledge-base content</small>
                    </div>
                  </div>
                </div>

                <p>
                  Document management functionality is not connected yet.
                </p>

              </div>

            </section>

          </>

        )}

      </main>

    </div>
  )
}

export default App
