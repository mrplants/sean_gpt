import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthService } from '../services/authService';
import LoginModal from './LoginSignupModal';

const TitleBar = () => {
  const { logout, user, authToken } = useAuthService();
  const [isReferModalOpen, setIsReferModalOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const detailsRef = useRef(null);

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
            { authToken && (<li> <Link to="/chat" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">Chat</Link> </li>) }
            <li> <Link to="/about" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">About</Link> </li>
            <li> <Link to="/faq" onClick={closeDetails} className="btn btn-sm btn-ghost normal-case my-1">FAQ</Link> </li>
          </ul>
        </details>
      <Link to="/" className="prose prose-xl dark:prose-invert prose-slate mx-3">SeanGPT</Link>
      <div className="hidden lg:flex">
        { authToken && (<Link to="/chat" className="btn btn-sm btn-ghost normal-case mx-1">Chat</Link>) }
        <Link to="/about" className="btn btn-sm btn-ghost normal-case mx-1">About</Link>
        <Link to="/faq" className="btn btn-sm btn-ghost normal-case mx-1">FAQ</Link>
      </div>
      </div>
      <div className="navbar-end">
        {authToken ? (
          <>
            <div>
              <button className="btn btn-sm btn-ghost mx-2" onClick={() => setIsReferModalOpen(true)}>Refer friends!</button>
            </div>
            <button onClick={logout} className="btn btn-sm btn-outline btn-primary">
              Logout
            </button>
            {/* This modal is the refer-friends dialog */}
            <dialog className={`modal modal-bottom sm:modal-middle ${isReferModalOpen ? 'modal-open': ''}`}>
              <div className="modal-box">
                <p className="text-lg text-center">Share this referral code with your friends!</p>
                <h3 className="font-bold text-lg text-center">{user.referral_code}</h3>
              </div>
              <form method="dialog" className="modal-backdrop">
                <button onClick={() => setIsReferModalOpen(false)}>close</button>
              </form>
            </dialog>
          </>
        ) : (
          <>
            <button onClick={() => setIsLoginModalOpen(true)} className="btn btn-sm btn-primary">
              Login | Signup
            </button>
            <LoginModal isOpen={isLoginModalOpen} setIsOpen={setIsLoginModalOpen}/>
          </>
        )}
      </div>
    </header>
  );
};

export default TitleBar;