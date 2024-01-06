import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PhoneNumberInput from '../../components/PhoneNumberInput';

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
          <h1 className="text-5xl font-bold">SeanGPT</h1>
          <form className="card-body" onSubmit={handleSubmit}>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Phone</span>
              </label>
              <PhoneNumberInput
                className="input input-bordered" 
                required 
                value={username}
                setValue={setUsername}
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
            <br/>
            <a href="sms:+15104548054" className="link link-primary">Text (510)454-8054 to sign up!</a>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
