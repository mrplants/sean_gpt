import { Outlet } from "react-router-dom";
import { Link } from 'react-router-dom';

import TitleBar from "../../components/TitleBar";

const Root = () => {
  return (
  <div className="grid grid-rows-[auto,1fr] h-screen">
  <TitleBar />

  <main className="overflow-auto">
    <Outlet />
  </main>
  <footer className="footer p-4 bg-neutral text-neutral-content">
    <nav className="grid grid-flow-col gap-4">
      <Link to="/contact" className="link link-hover">Contact</Link>
      <Link to="/tos" className="link link-hover">Terms of service</Link>
      <Link to="/privacy" className="link link-hover">Privacy policy</Link>
    </nav>
  </footer>
</div>
)

};

export default Root;