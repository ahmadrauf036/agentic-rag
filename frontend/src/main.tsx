import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";
import { AuthProvider } from "@/context/AuthContext";
import { SessionsProvider } from "@/context/SessionsContext";
import { ToastProvider } from "@/components/ui/Toast";
import { DocumentsProvider } from "./context/DocumentContext";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <SessionsProvider>
            <DocumentsProvider>
            <App />
            </DocumentsProvider>
          </SessionsProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </StrictMode>,
);