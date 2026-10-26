export type Etat = {
  demande_id?: string;
  demande_brute?: string;
  pieces_jointes?: string[];
  demande?: { article?: string; quantite?: number; service?: string; budget?: number };
  question_demandeur?: string | null;
  document?: Record<string, unknown> | null;
  fournisseurs?: { nom: string; prix_unitaire: number; autorise: boolean }[];
  violations?: string[];
  ecarts?: string[];
  statut?: string;
  commande_id?: string | null;
  journal?: { etape: string; raison: string; ts: string }[];
};

export type Vue = { id: string; etat: Etat; en_attente: string[] };

async function appel<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const deposer = async (f: File) => {
  const fd = new FormData();
  fd.append("fichier", f);
  return appel<{ chemin: string }>("/api/documents", { method: "POST", body: fd });
};
export const creerDemande = (texte: string, pieces_jointes: string[]) =>
  appel<Vue>("/api/demandes", json({ texte, pieces_jointes }));
export const lireDemande = (id: string) => appel<Vue>(`/api/demandes/${id}`);
export const reprendre = (id: string, champs: Record<string, unknown>) =>
  appel<Vue>(`/api/demandes/${id}/reprendre`, json({ champs }));
