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
    g.invoke({"demande_brute": "10 écrans 27 pouces pour Design"}, cfg("t2"))
    assert g.get_state(cfg("t2")).next == ("attente_decision",)
    g.update_state(cfg("t2"), {"decision": "refus", "motif": "hors budget"})
    g.invoke(None, cfg("t2"))
    v = g.get_state(cfg("t2")).values
    assert v["statut"] == "refusee" and not v.get("commande_id")


def test_demande_vide_demande_precisions():
    g = construire()
    g.invoke({"demande_brute": ""}, cfg("t3"))
    st = g.get_state(cfg("t3"))
    assert st.next == ("attente_precisions",)
    assert st.values["statut"] == "incomplet"
    assert st.values.get("question_demandeur") is not None


def test_demande_invalide_demande_precisions():
    g = construire()
    g.invoke({"demande_brute": "x"}, cfg("t4"))
    st = g.get_state(cfg("t4"))
    assert st.next == ("attente_precisions",)
    assert st.values["statut"] == "incomplet"
    assert st.values.get("question_demandeur") is not None


def test_reprise_apres_attente_precisions():
    g = construire()
    # 1. Demande initiale incomplète -> pause attente_precisions avec statut incomplet et question
    g.invoke({"demande_brute": "Je voudrais des écrans pour mon équipe"}, cfg("t5"))
    st1 = g.get_state(cfg("t5"))
    assert st1.next == ("attente_precisions",)
    assert st1.values["statut"] == "incomplet"
    assert st1.values.get("question_demandeur") is not None

    # 2. Le demandeur apporte les précisions (quantité et service)
    g.update_state(cfg("t5"), {"demande_brute": "10 écrans 27 pouces pour le service Design"})
    g.invoke(None, cfg("t5"))

    # 3. L'agent reprend, valide l'extraction et poursuit jusqu'à la validation
    st2 = g.get_state(cfg("t5"))
    assert st2.next == ("attente_decision",)
    assert st2.values.get("demande") is not None
    assert st2.values["demande"]["quantite"] == 10


