import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import authService from '../services/authService';
import LoginModal from './LoginModal';

const TitleBar = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());

  useEffect(() => {
    setIsAuthenticated(authService.isAuthenticated());
  }, []);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(authService.isAuthenticated());
  };

  const handleLogin = () => {
    const modal = document.getElementById('login_modal');
    if (modal && modal.showModal) {
      modal.showModal();
    }
  };

  return (
    <header className="navbar bg-base-100 px-4 py-2">
      <div className="flex-1">
        <Link to="/" className="btn btn-ghost normal-case text-xl">SeanGPT</Link>
      </div>
      <div className="flex-none">
        {isAuthenticated ? (
          <button onClick={handleLogout} className="btn btn-primary">
            Logout
          </button>
        ) : (
          <>
            <button onClick={handleLogin} className="btn btn-primary">
              Login
            </button>
            <LoginModal onLogin={() => setIsAuthenticated(true)} />
          </>
        )}
      </div>
    </header>
  );
};

export default TitleBar;