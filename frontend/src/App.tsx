import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { ContactDetail } from "./components/ContactDetail";
import { ContactForm } from "./components/ContactForm";
import { ContactList } from "./components/ContactList";
import { NeedList } from "./components/NeedList";
import { RelationshipGraph } from "./components/RelationshipGraph";
import "./App.css";

function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return (localStorage.getItem("theme") as "light" | "dark") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <div className="app">
      <nav>
        <Link to="/contacts">Contacts</Link>
        <Link to="/graph">Graph</Link>
        <Link to="/needs">Needs</Link>
        <button className="btn btn-small theme-toggle" onClick={toggleTheme}>
          {theme === "light" ? "Dark" : "Light"}
        </button>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<ContactList />} />
          <Route path="/contacts" element={<ContactList />} />
          <Route path="/contacts/new" element={<ContactForm />} />
          <Route path="/contacts/:id" element={<ContactDetail />} />
          <Route path="/contacts/:id/edit" element={<ContactForm />} />
          <Route path="/graph" element={<RelationshipGraph />} />
          <Route path="/needs" element={<NeedList />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
