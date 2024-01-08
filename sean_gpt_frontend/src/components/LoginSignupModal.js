import { useState, forwardRef, useImperativeHandle } from 'react';
import toast from 'react-hot-toast';

import PhoneNumberInput from './PhoneNumberInput';
import { useAuthService } from '../services/authService';

const Login = forwardRef(({ onLogin }, ref) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSignupForm, setIsSignupForm] = useState(false);
  const { attemptLogin } = useAuthService();

  const openModal = () => {
    setIsModalOpen(true);
    const modal = document.getElementById('login_modal');
    if (modal && modal.showModal) {
      modal.showModal();
    }
};

  const closeModal = () => {
    const modal = document.getElementById('login_modal');
    if (modal && modal.close) {
      modal.close();
    }
  setIsModalOpen(false);
  };

  useImperativeHandle(ref, () => ({
    openModal,
    closeModal
  }));

  const loginFormSubmit = async (event) => {
    event.preventDefault();

    try {
      await attemptLogin(username, password);
      // Close the modal if login is successful
      const modal = document.getElementById('login_modal');
      if (modal && modal.close) {
        modal.close();
      }
    } catch (error) {
      setUsername('');
      setPassword('');
    }
  };

  /**
   * Handle the account creation process.
   * @param {Event} event - The event triggered on form submission.
   */
  const createAccount = async (event) => {
    event.preventDefault();

    // Basic validation can be done here or in the form inputs
    if (!username || !password || !referralCode) {
      toast.error('Please fill in all fields.');
      return;
    }

    // Prepare the data to be sent to the server
    const accountData = {
      user: {
        phone: username,
        password: password,
      },
      referral_code: referralCode,
    };

    try {
      // Replace 'YOUR_ENDPOINT_URL' with the actual endpoint URL
      const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(accountData),
      });

      // Check if the request was successful
      if (response.ok) {
        const data = await response.json();
        // Handle successful account creation, e.g., updating the UI or redirecting
        toast.success('Account created successfully!');
        closeModal(); // Close the modal on successful account creation
        loginFormSubmit(event);
      } else {
        // Handle errors, e.g., displaying a message to the user
        const errorData = await response.json();
        console.error('Account creation failed:', errorData);
        toast.error(errorData.detail);
      }
    } catch (error) {
      // Handle network errors
      console.error('Network error:', error);
      toast.error('Failed to create account. Please try again later.');
    }
  };

  return (
  <dialog id="login_modal" className="modal modal-bottom sm:modal-middle">
    <div className="modal-box">
      <div className="max-w-md">
        {isModalOpen &&
        <form className="card-body" onSubmit={isSignupForm ? createAccount : loginFormSubmit}>
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
          <div className={`form-control ${isSignupForm ? '':'hidden'}`}>
            <label className="label">
              <span className="label-text">Referral Code</span>
            </label>
            <input
              type="text"
              placeholder="XXXXXXXX"
              className="input input-bordered"
              {...(isSignupForm ? { required: true } : {})}
              value={referralCode}
              onChange={(e) => setReferralCode(e.target.value)}
            />
          </div>
          <div className={`form-control mt-4 ${isSignupForm ? 'hidden':''}`}>
            <button className="btn btn-primary" type='submit'>Login</button>
          </div>
          <div className={`form-control mt-4 ${isSignupForm ? '':'hidden'}`}>
            <button className="btn btn-primary" type='submit'>Signup</button>
          </div>
          <div className={`form-control ${isSignupForm ? 'hidden':''}`}>
            <button className="btn btn-accent" onClick={() => setIsSignupForm(true)}>New Account?</button>
          </div>
          <div className={`form-control ${isSignupForm ? '':'hidden'}`}>
            <button className="btn btn-accent" onClick={() => setIsSignupForm(false)}>Have an account?</button>
          </div>
          {/* <br/>
          <a href="sms:+15104548054" className="link link-primary" style={{textAlign: 'center'}}>Text (510)454-8054 to sign up!</a> */}
        </form>
        }
      </div>
    </div>
    <form method="dialog" className="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
  );
});

export default Login;
