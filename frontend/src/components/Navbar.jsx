import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';

export function Navbar() {
  const location = useLocation();
  const { workspace } = useWorkspace();

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const totalItems =
    (workspace?.diseases?.length || 0) +
    (workspace?.genes?.length || 0) +
    (workspace?.comparisons?.length || 0) +
    (workspace?.records?.length || 0) +
    (workspace?.notes?.length || 0);

  return (
    <header style={{
      background: 'var(--surface)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0.7rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        {/* Product Identity */}
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
          <span style={{
            color: 'var(--text-primary)',
            fontWeight: 700,
            fontSize: '1.05rem',
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            fontFamily: 'var(--font-heading)'
          }}>
            Research Explorer
          </span>
          <span style={{
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
            fontWeight: 500,
            fontFamily: 'var(--font-body)'
          }}>
            Disease–Gene Evidence Database
          </span>
        </Link>

        {/* Minimal & Premium Navigation Links */}
        <nav aria-label="Main Navigation">
          <ul style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            listStyle: 'none',
            margin: 0,
            padding: 0,
            flexWrap: 'wrap'
          }}>
            <li>
              <Link to="/" style={navLinkStyle(isActive('/'))}>
                Search
              </Link>
            </li>
            <li>
              <Link to="/graph" style={navLinkStyle(isActive('/graph'))}>
                Explore Network
              </Link>
            </li>
            <li>
              <Link to="/compare" style={navLinkStyle(isActive('/compare'))}>
                Compare
              </Link>
            </li>
            <li>
              <Link to="/workspace" style={navLinkStyle(isActive('/workspace'))}>
                Workspace
                {totalItems > 0 && (
                  <span style={{
                    background: 'var(--surface-sage)',
                    color: 'var(--accent)',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    fontFamily: 'var(--font-heading)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '0.1rem 0.35rem',
                    marginLeft: '0.4rem',
                    border: '1px solid var(--border-strong)'
                  }}>
                    {totalItems}
                  </span>
                )}
              </Link>
            </li>
            <li>
              <Link to="/about" style={navLinkStyle(isActive('/about'))}>
                About
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

const navLinkStyle = (active) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '0.4rem 0.75rem',
  fontSize: '0.875rem',
  fontWeight: active ? 600 : 500,
  fontFamily: 'var(--font-body)',
  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
  background: active ? 'var(--surface-muted)' : 'transparent',
  border: active ? '1px solid var(--border-subtle)' : '1px solid transparent',
  borderRadius: 'var(--radius-sm)',
  textDecoration: 'none',
  transition: 'var(--transition-fast)'
});

export default Navbar;
