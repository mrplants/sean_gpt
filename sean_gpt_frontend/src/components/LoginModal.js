import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PhoneNumberInput from './PhoneNumberInput';

import authService from '../services/authService';

const Login = ({ onLogin }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const prior = location.state?.from?.pathname || '/';

  const handleSubmit = async (event) => {
    event.preventDefault();
  
    try {
      await authService.login(username, password);
      // Close the modal if login is successful
      const modal = document.getElementById('login_modal');
      if (modal && modal.close) {
        modal.close();
      }
      navigate(prior, { replace: true });
      onLogin(); // Call the onLogin function passed in as a prop
    } catch (error) {
      setUsername('');
      setPassword('');
    }
  };
  
  return (
  <dialog id="login_modal" className="modal modal-bottom sm:modal-middle">
    <div className="modal-box">
      <div className="max-w-md">
        <form className="card-body" onSubmit={handleSubmit}>
          <div className="form-control">
            <label className="label">
              <span className="label-text">Phone</span>
            </label>
            <PhoneNumberInput
              className="input input-bordered" 
              required 
              value={username}
              setValue={setUsername} />
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
          <a href="sms:+15104548054" className="link link-primary" style={{textAlign: 'center'}}>Text (510)454-8054 to sign up!</a>
        </form>
      </div>
    </div>
    <form method="dialog" className="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
  );
};

export default Login;
