import { useState } from 'react';

const Login = () => {
  // State to store input values
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Function to handle form submission
  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior

    // Create form data
    const formData = new FormData(event.target);
    formData.append('grant_type', 'password');
    const formJson = Object.fromEntries(formData.entries());
    console.log(formJson);

    try {
      const response = await fetch('/token', { // Change the URL to your authentication endpoint
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Login successful:', data);

      // Here you would typically store the auth tokens in state or some form of storage (like localStorage)
      // and redirect the user or perform some other action
    } catch (error) {
      console.error('Login failed:', error);
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
            <input type="text" placeholder="" name='username' className="input input-bordered" required />
            </div>
            <div className="form-control">
            <label className="label">
                <span className="label-text">Password</span>
            </label>
            <input type="password" placeholder="" name='password' className="input input-bordered" required />
            </div>
            <div className="form-control mt-6">
            <button className="btn btn-primary" type='submit'>Login</button>
            </div>
        </form>
        </div>
    </div>
    </div>
  );
}

export default Login;
