import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import authService from '../../services/authService';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const prior = location.state?.from?.pathname || '/';

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      await authService.login(username, password);
      navigate(prior, { replace: true });
    } catch (error) {
      setUsername('');
      setPassword('');
    }
  };

  return (
    <div className="hero min-h-screen bg-base-200">
      <div className="hero-content text-center">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold">(Artificial) Sean</h1>
          <form className="card-body" onSubmit={handleSubmit}>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Username</span>
              </label>
              <input 
                type="text" 
                placeholder="" 
                className="input input-bordered" 
                required 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Password</span>
              </label>
              <input 
                type="password" 
                placeholder="" 
                className="input input-bordered" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-control mt-6">
              <button className="btn btn-primary" type='submit'>Login</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
