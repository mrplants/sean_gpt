import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuthService } from '../services/authService';
import LoginModal from './LoginModal';

const TitleBar = () => {
  const { logout, isLoggedIn } = useAuthService();

  const loginModalRef = useRef(null);
  const detailsRef = useRef(null);

  const handleLogin = () => {
    loginModalRef.current.openModal();
  };

  const closeDetails = () => {
    if (detailsRef.current) {
      detailsRef.current.removeAttribute('open');
    }
  };

  return (
    <header className="navbar bg-base-200">
      <div className="navbar-start">
        <details className="dropdown" ref={detailsRef}>
          <summary tabIndex={0} role="button" className="btn btn-ghost lg:hidden">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" /></svg>
          </summary>
          <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
            { isLoggedIn && (<li> <Link to="/chat" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">Chat</Link> </li>) }
            <li> <Link to="/about" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">About</Link> </li>
            <li> <Link to="/contact" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">Contact</Link> </li>
            <li> <Link to="/faq" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">FAQ</Link> </li>
            <li> <Link to="/tos" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">Terms of Service</Link> </li>
          </ul>
        </details>
      <Link to="/" className="prose prose-xl dark:prose-invert prose-slate mx-3">SeanGPT</Link>
      <div className="hidden lg:flex">
        { isLoggedIn && (<Link to="/chat" className="btn btn-sm btn-ghost normal-case mx-2">Chat</Link>) }
        <Link to="/about" className="btn btn-sm btn-ghost normal-case mx-2">About</Link>
        <Link to="/contact" className="btn btn-sm btn-ghost normal-case mx-2">Contact</Link>
        <Link to="/faq" className="btn btn-sm btn-ghost normal-case mx-2">FAQ</Link>
        <Link to="/tos" className="btn btn-sm btn-ghost normal-case mx-2">Terms of Service</Link>
      </div>
      </div>
      <div className="navbar-end">
        {isLoggedIn ? (
          <button onClick={logout} className="btn btn-sm btn-ghost">
            Logout
          </button>
        ) : (
          <>
            <button onClick={handleLogin} className="btn btn-sm btn-primary">
              Login
            </button>
            <LoginModal ref={loginModalRef}/>
          </>
        )}
      </div>
    </header>
  );
};

export default TitleBar;