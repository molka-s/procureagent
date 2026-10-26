from app.agent.audit import etape
from app.agent import tools


@etape("enrichir")
def enrichir(s):
    return {"_raison": "Dossier enrichi (demande + document)"}


@etape("rechercher_fournisseurs")
def rechercher_fournisseurs(s):
    f = tools.chercher_fournisseurs(s.get("demande", {}).get("article", ""))
    return {"fournisseurs": f, "_raison": f"{len(f)} fournisseur(s) trouvé(s)"}


@etape("verifier_regles")
def verifier_regles(s):
    d = s.get("demande", {})
    f = (s.get("fournisseurs") or [{}])[0]
    montant = f.get("prix_unitaire", 0) * d.get("quantite", 0)
    budget_ok = tools.verifier_budget(d.get("service", ""), montant)
    violations = tools.verifier_regles(montant, f.get("autorise", False))
    if not budget_ok:
        violations.append("budget insuffisant")
    return {"budget_ok": budget_ok, "violations": violations, "_raison": f"montant={montant}"}


@etape("preparer_dossier")
def preparer_dossier(s):
    ok = not s.get("violations")
    return {"controles_ok": ok, "ecarts": s.get("violations", []), "_raison": "Dossier prêt" if ok else "Écarts signalés"}


@etape("signaler_probleme")
def signaler_probleme(s):
    return {"statut": "probleme_signale", "_raison": "; ".join(s.get("violations", []))}


@etape("attente_regularisation")
def attente_regularisation(s):
    return {"_raison": "Décision humaine : dossier régularisable ?"}


@etape("bloquer")
def bloquer(s):
    return {"statut": "bloque", "_raison": s.get("motif") or "Dossier non régularisable"}
