"""Graphe d'états de l'agent (reflète docs/diagramme.png).
Pauses humaines : interrupt_before sur les noeuds attente_*."""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.state import EtatAgent
from app.agent.nodes import analyse as a, controle as c, validation as v

POINTS_ARRET = ["attente_precisions", "attente_correction_ocr",
                "attente_regularisation", "attente_decision"]


def ocr_ok(s): return "oui" if s.get("ocr_fiable") else "non"
def controles_ok(s): return "oui" if s.get("controles_ok") else "non"
def regularisable(s): return "oui" if s.get("regularisable") else "non"
def decision(s): return s.get("decision") or "refus"


def construire(checkpointer=None):
    g = StateGraph(EtatAgent)
    for nom, fn in [
        ("reception", a.reception), ("comprendre", a.comprendre),
        ("attente_precisions", a.attente_precisions),
        ("extraire_document", a.extraire_document), ("verifier_ocr", a.verifier_ocr),
        ("attente_correction_ocr", a.attente_correction_ocr),
        ("enrichir", c.enrichir), ("rechercher_fournisseurs", c.rechercher_fournisseurs),
        ("verifier_regles", c.verifier_regles), ("preparer_dossier", c.preparer_dossier),
        ("signaler_probleme", c.signaler_probleme),
        ("attente_regularisation", c.attente_regularisation), ("bloquer", c.bloquer),
        ("presenter_validateur", v.presenter_validateur), ("attente_decision", v.attente_decision),
        ("corriger_dossier", v.corriger_dossier), ("creer_commande", v.creer_commande),
        ("notifier", v.notifier), ("journaliser", v.journaliser),
        ("enregistrer_refus", v.enregistrer_refus),
    ]:
        g.add_node(nom, fn)

    g.add_edge(START, "reception")
    g.add_edge("reception", "comprendre")
    g.add_conditional_edges("comprendre", lambda s: ("non_info" if not s.get("infos_suffisantes")
                            else ("doc" if s.get("pieces_jointes") else "sans_doc")),
                            {"non_info": "attente_precisions", "doc": "extraire_document", "sans_doc": "enrichir"})
    g.add_edge("attente_precisions", "comprendre")
    g.add_edge("extraire_document", "verifier_ocr")
    g.add_conditional_edges("verifier_ocr", ocr_ok, {"oui": "enrichir", "non": "attente_correction_ocr"})
    g.add_edge("attente_correction_ocr", "verifier_ocr")
    g.add_edge("enrichir", "rechercher_fournisseurs")
    g.add_edge("rechercher_fournisseurs", "verifier_regles")
    g.add_edge("verifier_regles", "preparer_dossier")
    g.add_conditional_edges("preparer_dossier", controles_ok,
                            {"oui": "presenter_validateur", "non": "signaler_probleme"})
    g.add_edge("signaler_probleme", "attente_regularisation")
    g.add_conditional_edges("attente_regularisation", regularisable, {"oui": "enrichir", "non": "bloquer"})
    g.add_edge("bloquer", END)
    g.add_edge("presenter_validateur", "attente_decision")
    g.add_conditional_edges("attente_decision", decision,
                            {"approbation": "creer_commande", "refus": "enregistrer_refus",
                             "correction": "corriger_dossier"})
    g.add_edge("corriger_dossier", "enrichir")
    g.add_edge("creer_commande", "notifier")
    g.add_edge("notifier", "journaliser")
    g.add_edge("journaliser", END)
    g.add_edge("enregistrer_refus", END)
    return g.compile(checkpointer=checkpointer or MemorySaver(), interrupt_before=POINTS_ARRET)
