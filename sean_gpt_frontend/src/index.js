import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
  RouterProvider,
} from "react-router-dom";
import { Toaster } from 'react-hot-toast';

import './index.css';
import { AuthProvider } from './services/authService';

import Root from './routes/Root';
import Home from './routes/Home';
import TermsOfService from './routes/TermsOfService';
import FAQ from './routes/FAQ';
import About from './routes/About';
import Contact from './routes/Contact';
import ErrorPage from './components/ErrorPage';
import Chat from './routes/Chat';
import PrivacyPolicy from './routes/PrivacyPolicy';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path='/' element={<Root />} errorElement={<ErrorPage />}>
      <Route index element={<Home />} />
      <Route path='chat' element={<Chat />} />
      <Route path='tos' element={<TermsOfService />} />
      <Route path='faq' element={<FAQ />} />
      <Route path='about' element={<About />} />
      <Route path='contact' element={<Contact />} />
      <Route path='privacy' element={<PrivacyPolicy />} />
    </Route>
  )
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AuthProvider>      
      <RouterProvider router={router} />
      <Toaster />
    </AuthProvider>
  </React.StrictMode>
);