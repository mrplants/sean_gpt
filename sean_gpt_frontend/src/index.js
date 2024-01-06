import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import { Toaster } from 'react-hot-toast';

import './index.css';

import Root from './routes/Root';
import Login from './routes/Login';
import Chat from './routes/Chat';
import PrivateRoute from "./routes/PrivateRoute";

import ErrorPage from './components/ErrorPage';

const router = createBrowserRouter([
  {
    path: "/",
    element: (
        <Root>
          <About />
          <FAQ />
          <TermsOfService />
        </Root>
    ),
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <Chat /> },
    ],
  },
  {
    path: "/login",
    element: <Login />,
  },
]);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
    <Toaster />
  </React.StrictMode>
);