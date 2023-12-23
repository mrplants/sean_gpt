import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import authService from '../services/authService';

const TitleBar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <header className="navbar bg-base-100 px-4 py-2">
      <div className="flex-1">
        <Link to="/" className="btn btn-ghost normal-case text-xl">(Artificial) Sean</Link>
      </div>
      <div className="flex-none">
        <button onClick={handleLogout} className="btn btn-primary">
          Logout
        </button>
      </div>
    </header>
  );
};

export default TitleBar;
