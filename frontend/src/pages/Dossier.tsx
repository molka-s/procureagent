import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Vue, lireDemande, reprendre } from "../api";

export default function Dossier() {
  const { id = "" } = useParams();
  const [vue, setVue] = useState<Vue | null>(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    lireDemande(id).then(setVue).catch((e) => setErreur(e.message));
  }, [id]);

  const agir = useCallback(
    async (champs: Record<string, unknown>) => {
      try {
        setErreur("");
        setVue(await reprendre(id, champs));
      } catch (e) {
        setErreur((e as Error).message);
      }
    },
    [id]
  );

  if (!vue) return <p>{erreur || "Chargement…"}</p>;
  const { etat, en_attente } = vue;
  const pause = en_attente[0];

  return (
    <>
      <div className="carte">
        <h2>
          Dossier <small>{id.slice(0, 8)}</small> <span className={`badge ${etat.statut}`}>{etat.statut}</span>
        </h2>
        <p><b>Demande :</b> {etat.demande_brute}</p>
        {etat.demande && (
          <p>
            <b>Extrait :</b> {etat.demande.quantite} × {etat.demande.article} — {etat.demande.service}
            {etat.demande.budget ? ` — budget ${etat.demande.budget} €` : ""}
          </p>
        )}
        {etat.fournisseurs?.map((f) => (
          <p key={f.nom}><b>Fournisseur :</b> {f.nom} ({f.prix_unitaire} € / unité){!f.autorise && " — non autorisé"}</p>
        ))}
        {!!etat.ecarts?.length && <p className="erreur"><b>Écarts :</b> {etat.ecarts.join(" ; ")}</p>}
        {etat.commande_id && <p><b>Commande créée :</b> {etat.commande_id}</p>}
      </div>

      {pause && <Action pause={pause} vue={vue} agir={agir} />}
      {erreur && <p className="erreur">{erreur}</p>}

      <div className="carte">
        <h3>Journal d'audit</h3>
        <table>
          <thead><tr><th>Heure</th><th>Étape</th><th>Raison</th></tr></thead>
          <tbody>
            {etat.journal?.map((j, i) => (
              <tr key={i}><td>{new Date(j.ts).toLocaleTimeString("fr-FR")}</td><td>{j.etape}</td><td>{j.raison}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Action({ pause, vue, agir }: { pause: string; vue: Vue; agir: (c: Record<string, unknown>) => void }) {
  const [texte, setTexte] = useState("");

  if (pause === "attente_decision")
    return (
      <div className="carte action">
        <h3>Validation requise</h3>
        <input placeholder="Motif (refus ou correction)" value={texte} onChange={(e) => setTexte(e.target.value)} />
        <div className="boutons">
          <button className="ok" onClick={() => agir({ decision: "approbation" })}>Approuver</button>
          <button className="ko" onClick={() => agir({ decision: "refus", motif: texte })}>Refuser</button>
          <button onClick={() => agir({ decision: "correction", motif: texte })}>Demander une correction</button>
        </div>
      </div>
    );

  if (pause === "attente_precisions")
    return (
      <div className="carte action">
        <h3>Informations manquantes</h3>
        <textarea rows={3} value={texte} onChange={(e) => setTexte(e.target.value)} placeholder="Précisions du demandeur…" />
        <button onClick={() => agir({ demande_brute: `${vue.etat.demande_brute ?? ""}\n${texte}` })}>Envoyer</button>
      </div>
    );

  if (pause === "attente_correction_ocr")
    return <CorrectionOCR doc={vue.etat.document ?? {}} agir={agir} />;

  if (pause === "attente_regularisation")
    return (
      <div className="carte action">
        <h3>Contrôles non satisfaits : le dossier est-il régularisable ?</h3>
        <div className="boutons">
          <button className="ok" onClick={() => agir({ regularisable: true })}>Oui, relancer</button>
          <button className="ko" onClick={() => agir({ regularisable: false, motif: "Non régularisable" })}>Non, clôturer</button>
        </div>
      </div>
    );

  return null;
}

// Écran de vérification OCR (version minimale) : document à gauche, champs modifiables à droite.
function CorrectionOCR({ doc, agir }: { doc: Record<string, unknown>; agir: (c: Record<string, unknown>) => void }) {
  const [brut, setBrut] = useState(JSON.stringify(doc, null, 2));
  const [err, setErr] = useState("");
  function valider() {
    try {
      // Après correction humaine, la confiance est considérée maximale.
      agir({ document: { ...JSON.parse(brut), confiance_min: 1 } });
    } catch {
      setErr("JSON invalide");
    }
  }
  return (
    <div className="carte action">
      <h3>Vérification du document</h3>
      <div className="deux">
        <div className="apercu">Aperçu du document (à brancher)</div>
        <textarea rows={12} value={brut} onChange={(e) => setBrut(e.target.value)} />
      </div>
      {err && <p className="erreur">{err}</p>}
      <button className="ok" onClick={valider}>Valider les données</button>
    </div>
  );
}
