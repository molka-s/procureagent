import { Link, Route, Routes } from "react-router-dom";
import Demande from "./pages/Demande";
import Dossier from "./pages/Dossier";

export default function App() {
  return (
    <>
      <header>
        <Link to="/">ProcureAgent</Link>
        <span>Demandes d'achat assistées par IA</span>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Demande />} />
          <Route path="/dossiers/:id" element={<Dossier />} />
        </Routes>
      </main>
    </>
  );
}
