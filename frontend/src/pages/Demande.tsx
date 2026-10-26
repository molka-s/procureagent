import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { creerDemande, deposer } from "../api";

export default function Demande() {
  const [texte, setTexte] = useState("");
  const [fichier, setFichier] = useState<File | null>(null);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const nav = useNavigate();

  async function soumettre(e: FormEvent) {
    e.preventDefault();
    setEnvoi(true);
    setErreur("");
    try {
      const pieces = fichier ? [(await deposer(fichier)).chemin] : [];
      const vue = await creerDemande(texte, pieces);
      nav(`/dossiers/${vue.id}`);
    } catch (err) {
      setErreur((err as Error).message);
      setEnvoi(false);
    }
  }

  return (
    <form className="carte" onSubmit={soumettre}>
      <h2>Nouvelle demande d'achat</h2>
      <label>
        Votre besoin
        <textarea
          rows={5}
          required
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          placeholder="Il me faut 10 écrans 27 pouces pour le service design, budget autour de 3 000 €…"
        />
      </label>
      <label>
        Devis ou facture (PDF, JPG, PNG)
        <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFichier(e.target.files?.[0] ?? null)} />
      </label>
      {erreur && <p className="erreur">{erreur}</p>}
      <button disabled={envoi || !texte.trim()}>{envoi ? "Traitement…" : "Envoyer"}</button>
    </form>
  );
}
