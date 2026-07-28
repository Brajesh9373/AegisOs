import React from 'react';

export function Header({ onLogout }: { onLogout: () => void }) {
  return (
    <header
      style={{
        padding: '1rem',
        background: '#FFFFFF',
        color: '#333',
        borderBottom: '1px solid #eee',
        display: 'flex',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ fontWeight: 600, fontSize: '1.2rem' }}>aegisOS (Self-Hosted)</div>
      <button
        onClick={onLogout}
        style={{
          background: 'transparent',
          color: '#333',
          border: '1px solid #ccc',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Logout
      </button>
    </header>
  );
}
