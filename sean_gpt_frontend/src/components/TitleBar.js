import { useRef, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import authService from '../services/authService';
import LoginModal from './LoginModal';

const TitleBar = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());

  const loginModalRef = useRef(null);

  useEffect(() => {
    setIsAuthenticated(authService.isAuthenticated());
  }, []);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(authService.isAuthenticated());
  };

  const handleLogin = () => {
    loginModalRef.current.openModal();
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
            <LoginModal onLogin={() => setIsAuthenticated(true)} ref={loginModalRef}/>
          </>
        )}
      </div>
    </header>
  );
};

export default TitleBar;