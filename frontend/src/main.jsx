import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css"; // optional

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);


// ==============================
// Extra: public/index.html snippet (add BEFORE your bundle script)
// ==============================
// <script>
//   // Set your backend base here so phones on the same Wi‑Fi can access it
//   window.__API_BASE__ = "http://172.20.10.3:8001"; // ← 热点IP地址
// </script>
