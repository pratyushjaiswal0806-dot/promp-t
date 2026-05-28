import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles/tokens.css";
import "./styles/reset.css";
import "./styles/global.css";
import "./styles/layout.css";
import "./styles/components.css";
import "./styles/workbench.css";

createRoot(document.querySelector("#root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
