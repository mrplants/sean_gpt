import { Navigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';

const PrivateRoute = ({ children }) => {
  const location = useLocation();
  const authenticated = authService.isAuthenticated();

  if (!authenticated) {
    // Redirect them to the login page, but save the current location
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children; // Render child routes if authenticated
};

export default PrivateRoute;
