import { useAuthService } from "../services/authService"; // Import your auth provider
import About from './About';
import Chat from './Chat';

function Home() {
  const { isLoggedIn } = useAuthService(); // Replace with your actual auth check

  return isLoggedIn ? <Chat /> : <About />;
}

export default Home;