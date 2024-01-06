import toast from 'react-hot-toast';
import { jwtDecode } from "jwt-decode";

/**
 * Decodes the payload of a JWT and checks if it is expired.
 * @param {string} token - The JWT to be checked.
 * @returns {boolean} - Returns true if the token is expired, false otherwise.
 */
function isJwtExpired(token) {
  try {
    const decoded = jwtDecode(token);
    const currentTimestamp = Math.floor(Date.now() / 1000);
    return decoded.exp < currentTimestamp;
  } catch (e) {
    // Catch the error if the token cannot be decoded
    console.error("Token cannot be decoded:", e);
    return true;
  }
}

const TOKEN_KEY = 'authToken';

/**
 * Service to handle authentication. It uses the fetch API to send requests to the authentication
 * endpoint, and stores the token in localStorage.
 */
const authService = {
  /** 
    * Function to log the user in. It takes a username and password, and returns a promise
    * that resolves to the authentication response.
    * @param {string} username The username to log in with
    * @param {string} password The password to log in with
    * @returns {Promise} A promise that resolves to the authentication response
    */  
  login: async (username, password) => {
    const formData = new FormData();
    // These are the parameters necessary for OAuth2 password grant
    formData.append('username', username);
    formData.append('password', password);
    formData.append('grant_type', 'password');

    try {
      const response = await fetch('/user/token', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          toast.error('Invalid username or password');
        } else {
          toast.error('Login unsuccessful');
        }
        throw new Error(`HTTP error during login. Status: ${response.status}`);
      }

      // Store the token in localStorage
      const data = await response.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      toast.success('Login successful');
      return data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Function to log the user out. It clears the token from localStorage.
   */
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    toast.success('Logout successful');
  },

  /**
   * Function to check if the user is currently authenticated.
   * @returns {boolean} - Returns true if the user is authenticated, false otherwise.
   */
  isAuthenticated: () => {
    // Check if the token exists in localStorage
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      return false;
    }

    // Verify the token is not expired
    if (isJwtExpired(token)) {
      return false;
    }
    return true;
  },

  /**
   * Function to get the stored token.
   * @returns {string} - The stored token.
   */
  getToken: () => localStorage.getItem(TOKEN_KEY),
};

export default authService;
