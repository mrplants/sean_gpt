import { Outlet } from "react-router-dom";

import TitleBar from "../../components/TitleBar";

const Root = () => {
  return (
  <div className="grid grid-rows-[auto,1fr] h-screen">
  <TitleBar />

  <main className="overflow-auto">
    <Outlet />
  </main>
</div>
)

};

export default Root;