from app.agent.graph import construire


def cfg(t): return {"configurable": {"thread_id": t}}


def test_chemin_nominal_approbation():
    g = construire()
    g.invoke({"demande_brute": "10 écrans 27 pouces pour Design"}, cfg("t1"))
    assert g.get_state(cfg("t1")).next == ("attente_decision",)
    g.update_state(cfg("t1"), {"decision": "approbation"})
    g.invoke(None, cfg("t1"))
    v = g.get_state(cfg("t1")).values
    assert v["statut"] == "terminee" and v["commande_id"]
    assert len(v["journal"]) > 5


def test_refus_aucune_commande():
    g = construire()
    g.invoke({"demande_brute": "x"}, cfg("t2"))
    g.update_state(cfg("t2"), {"decision": "refus", "motif": "hors budget"})
    g.invoke(None, cfg("t2"))
    v = g.get_state(cfg("t2")).values
    assert v["statut"] == "refusee" and not v.get("commande_id")


def test_demande_vide_demande_precisions():
    g = construire()
    g.invoke({"demande_brute": ""}, cfg("t3"))
    assert g.get_state(cfg("t3")).next == ("attente_precisions",)
