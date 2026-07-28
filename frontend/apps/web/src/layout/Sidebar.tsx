import React from 'react';
import { Link } from 'react-router-dom';

export function Sidebar() {
  const linkStyle = {
    color: '#a0aec0',
    textDecoration: 'none',
    display: 'block',
    padding: '0.75rem 1rem',
    borderRadius: '4px',
    marginBottom: '0.5rem',
    transition: 'all 0.2s',
  };

  return (
    <div
      style={{
        width: '260px',
        background: '#1a202c',
        padding: '1.5rem 1rem',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <h3
        style={{
          margin: '0 0 2rem 1rem',
          color: '#edf2f7',
          fontSize: '1.5rem',
          letterSpacing: '1px',
        }}
      >
        AEGIS<span style={{ color: '#63b3ed' }}>AI</span>
      </h3>
      <nav style={{ flex: 1 }}>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          <li>
            <Link to="/dashboard" style={linkStyle}>
              Dashboard
            </Link>
          </li>
          <li>
            <Link to="/connectors" style={linkStyle}>
              Connector Center
            </Link>
          </li>
          <li>
            <Link to="/implementation" style={linkStyle}>
              Implementation Studio
            </Link>
          </li>
          <li>
            <Link to="/knowledge" style={linkStyle}>
              Knowledge Studio
            </Link>
          </li>
          <li>
            <Link to="/workspace" style={linkStyle}>
              Workspace
            </Link>
          </li>
          <li style={{ marginTop: '2rem' }}>
            <Link to="/settings" style={linkStyle}>
              Settings
            </Link>
          </li>
        </ul>
      </nav>
    </div>
  );
}
