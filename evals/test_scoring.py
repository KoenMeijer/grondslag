from evals import scoring


def test_ref_prefix_matcht_maar_geen_cijferbotsing():
    assert scoring.ref_matcht("Artikel 113", "Artikel 113, lid 2")
    assert scoring.ref_matcht("UAIV", "UAIV — beoogde toezichthouders in Nederland")
    # "Artikel 6" mag niet stiekem "Artikel 60" goedkeuren
    assert not scoring.ref_matcht("Artikel 6", "Artikel 60")


def test_retrieval_een_verwachte_ref_volstaat():
    assert scoring.score_retrieval(["Artikel 6", "Bijlage III"], ["Bijlage III, punt 4"])
    assert not scoring.score_retrieval(["Artikel 6"], ["Artikel 50"])
    assert scoring.score_retrieval([], ["wat dan ook"])  # abstentie-case: geen eis


def test_grounding_vereist_alle_markers_en_geen_verboden():
    assert scoring.score_grounding(["2 december 2027"], ["2 augustus 2026"],
                                   "De deadline is 2 december 2027.")
    assert not scoring.score_grounding(["2 december 2027"], ["2 augustus 2026"],
                                       "De deadline is 2 augustus 2026.")
    assert not scoring.score_grounding(["2 december 2027"], [], "Geen datum genoemd.")


def test_abstentie_eist_weigering_alleen_als_dat_moet():
    assert scoring.score_abstentie(True, "Dat kan ik niet beantwoorden op basis van mijn bronnen.")
    assert not scoring.score_abstentie(True, "Het antwoord is 42.")
    assert scoring.score_abstentie(False, "Het antwoord is 42.")
