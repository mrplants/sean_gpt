import { useAuthService } from '../../services/authService';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Chat = () => {
  const { isLoggedIn } = useAuthService();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/');
    }
  }, [isLoggedIn, navigate]);
  
  return (
    <div className="hero min-h-screen bg-base-200">
      <div className="hero-content text-center">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold">Under Construction</h1>
          <p className="py-6">Chat with SeanGPT via SMS at <a href="sms:+15104548054" className="link link-primary" style={{textAlign: 'center'}}>(510)454-8054</a>.</p>
        </div>
      </div>
    </div>
  );
}

export default Chat;
