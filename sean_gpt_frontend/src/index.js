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

import Root from './routes/Root';
import Login from './routes/Login';
import Chat from './routes/Chat';
import TermsOfService from './routes/TermsOfService';
import FAQ from './routes/FAQ';
import About from './routes/About';
// import PrivateRoute from "./routes/PrivateRoute";

import ErrorPage from './components/ErrorPage';

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path='/' element={<Root />} errorElement={<ErrorPage />}>
      <Route path='chat' element={<Chat />} />
      <Route path='tos' element={<TermsOfService />} />
      <Route path='faq' element={<FAQ />} />
      <Route path='about' element={<About />} />
    </Route>
  )
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
    <Toaster />
  </React.StrictMode>
);