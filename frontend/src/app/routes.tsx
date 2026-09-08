import { createBrowserRouter } from "react-router-dom";

import { DashboardPage } from "../features/dashboard/DashboardPage";
import { ImportPage } from "../features/import/ImportPage";
import { SystemPage } from "../features/system/SystemPage";
import { AppLayout } from "../shared/layout/AppLayout";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "import", element: <ImportPage /> },
      { path: "system", element: <SystemPage /> },
    ],
  },
]);
