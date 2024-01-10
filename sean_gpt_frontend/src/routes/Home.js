import { useAuthService } from "../services/authService"; // Import your auth provider
import About from './About';
import Chat from './Chat';

function Home() {
  const { authToken } = useAuthService(); // Replace with your actual auth check

  return authToken ? <Chat /> : <About />;
}

export default Home;