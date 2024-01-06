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
  // {
  //   path: "/",
  //   element: (
  //     <PrivateRoute>
  //       <Root />
  //     </PrivateRoute>
  //   ),
  //   errorElement: <ErrorPage />,
  //   children: [
  //     { index: true, element: <Chat /> },
  //   ],
  // },
  // {
  //   path: "/login",
  //   element: <Login />,
  // },
  {
    path: "/",
    element: <div className="hero min-h-screen bg-base-200">
    <div className="hero-content text-center">
      <div className="max-w-md">
        <h1 className="text-5xl font-bold">Under Construction</h1>
        <p className="py-6">Please stay tuned!  SeanGPT is coming soon.</p>
      </div>
    </div>
  </div>,
  },
]);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RouterProvider router={router} />
    <Toaster />
  </React.StrictMode>
);