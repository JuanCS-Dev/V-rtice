import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: '#0a0a0a',
          color: '#00ff00',
          fontFamily: 'monospace',
          padding: '20px'
        }}>
          <div style={{
            border: '2px solid #00ff00',
            borderRadius: '8px',
            padding: '30px',
            maxWidth: '800px',
            backgroundColor: '#1a1a1a'
          }}>
            <h1 style={{
              marginBottom: '20px',
              fontSize: '24px',
              textAlign: 'center'
            }}>
              ⚠️ VÉRTICE Error Handler
            </h1>

            <p style={{
              marginBottom: '15px',
              fontSize: '16px',
              color: '#ffaa00'
            }}>
              Algo deu errado. O sistema detectou um erro não tratado.
            </p>

            {this.state.error && (
              <div style={{
                backgroundColor: '#2a2a2a',
                padding: '15px',
                borderRadius: '4px',
                marginBottom: '15px',
                overflowX: 'auto'
              }}>
                <strong style={{ color: '#ff5555' }}>Error:</strong>
                <pre style={{
                  margin: '10px 0 0 0',
                  fontSize: '14px',
                  color: '#ff5555'
                }}>
                  {this.state.error.toString()}
                </pre>
              </div>
            )}

            {this.state.errorInfo && (
              <details style={{ marginBottom: '20px' }}>
                <summary style={{
                  cursor: 'pointer',
                  color: '#ffaa00',
                  marginBottom: '10px'
                }}>
                  Ver Stack Trace
                </summary>
                <div style={{
                  backgroundColor: '#2a2a2a',
                  padding: '15px',
                  borderRadius: '4px',
                  overflowX: 'auto'
                }}>
                  <pre style={{
                    margin: 0,
                    fontSize: '12px',
                    color: '#999'
                  }}>
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}

            <div style={{
              display: 'flex',
              gap: '10px',
              justifyContent: 'center'
            }}>
              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#00ff00',
                  color: '#000',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '14px'
                }}
              >
                Recarregar Página
              </button>

              <button
                onClick={() => window.location.href = '/'}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#333',
                  color: '#00ff00',
                  border: '1px solid #00ff00',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '14px'
                }}
              >
                Ir para Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
