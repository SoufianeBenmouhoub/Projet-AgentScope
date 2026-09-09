import { RouterProvider } from "react-router-dom";

import { router } from "./routes";

/** Point d'entrée de l'interface : routing et mise en page commune. */
export function App() {
  return <RouterProvider router={router} />;
}
