import React, { createContext, useContext, useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { jwtDecode } from 'jwt-decode';

// Constants
const TOKEN_KEY = 'authToken';

/**
 * Checks if the JWT token is expired.
 * @param {string} token - JWT token.
 * @returns {boolean} - True if expired, false otherwise.
 */
function isJwtExpired(token) {
  try {
    const decoded = jwtDecode(token);
    return decoded.exp < Math.floor(Date.now() / 1000);
  } catch (e) {
    console.error("Token cannot be decoded:", e);
    return true;
  }
}

// Create a Context
const AuthContext = createContext(null);

/**
 * Custom hook to use the authentication context.
 * @returns The authentication context.
 */
export function useAuthService() {
  return useContext(AuthContext);
}

/**
 * Provider component for authentication context.
 * @param {object} props - The props object.
 * @param {React.ReactNode} props.children - The children nodes.
 */
export function AuthProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token && !isJwtExpired(token)) {
        const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/user', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        // Check that the request was successful
        if (!response.ok) {
          // Remove the token from local storage if it is invalid
          localStorage.removeItem(TOKEN_KEY);
          setIsLoggedIn(false);
          setAuthToken(null);
          return;
        }

        const userData = await response.json();
        setUser(userData);
  
        setIsLoggedIn(true);
        setAuthToken(token);
      }
    };
  
    fetchUser();
  }, []);

  const attemptLogin = async (username, password) => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');

      const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/user/token', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorMsg = response.status === 401 ? 'Invalid username or password' : 'Login unsuccessful';
        toast.error(errorMsg);
        throw new Error(`HTTP error during login. Status: ${response.status}`);
      }

      const data = await response.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setAuthToken(data.access_token);
      toast.success('Login successful');

      const user_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/user', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });
      const userData = await user_response.json();
      setUser(userData);
      setIsLoggedIn(true);
  } catch (error) {
      console.error('Login attempt failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setIsLoggedIn(false);
    setAuthToken(null);
    setUser(null);
    toast.success('Logout successful');
  };

  return (
    <AuthContext.Provider value={{ attemptLogin, logout, isLoggedIn, authToken, user }}>
      {children}
    </AuthContext.Provider>
  );
}
