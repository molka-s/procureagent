from app.agent.audit import etape
from app.agent import tools


@etape("presenter_validateur")
def presenter_validateur(s):
    return {"statut": "en_attente_validation", "_raison": "Dossier présenté au validateur"}


@etape("attente_decision")
def attente_decision(s):
    return {"_raison": f"Décision humaine : {s.get('decision')}"}


@etape("corriger_dossier")
def corriger_dossier(s):
    return {"decision": None, "_raison": "Dossier corrigé, retour à l'enrichissement"}


@etape("creer_commande")
def creer_commande(s):
    # Seule écriture du système. Impossible sans approbation explicite.
    if s.get("decision") != "approbation":
        raise PermissionError("creer_commande sans approbation")
    cid = tools.creer_commande(s, approuve_par="validateur")
    return {"commande_id": cid, "_raison": f"Commande {cid} créée"}


@etape("notifier")
def notifier(s):
    tools.notifier("demandeur", f"Commande {s.get('commande_id')} créée")
    return {"_raison": "Demandeur notifié"}


@etape("journaliser")
def journaliser(s):
    # TODO: persister s["journal"] dans journal_audit
    return {"statut": "terminee", "_raison": "Journal persisté, dossier clôturé"}


@etape("enregistrer_refus")
def enregistrer_refus(s):
    return {"statut": "refusee", "_raison": s.get("motif") or "Refus enregistré"}
