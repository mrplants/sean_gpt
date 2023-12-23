import { useRouteError } from 'react-router-dom';

export default function ErrorPage() {
  const error = useRouteError();
  console.error(error);

  return (
    <div id="error-page" className="flex flex-col items-center justify-center h-screen bg-base-200 text-center">
      <div className="card w-96 bg-base-100 shadow-xl">
        <div className="card-body items-center text-center">
          <h2 className="card-title text-error">Oops!</h2>
          <p>Sorry, an unexpected error has occurred.</p>
          <p className="text-error">{error.statusText || error.message}</p>
        </div>
      </div>
    </div>
  );
}
