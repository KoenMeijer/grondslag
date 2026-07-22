from dataclasses import dataclass

from app.rag import prompt


@dataclass
class NepChunk:
    ref: str
    tekst: str


CHUNKS = [
    NepChunk(ref="Artikel 6, lid 2", tekst="Artikel 6, lid 2 (Classificatie): tekst A"),
    NepChunk(ref="Overweging 61", tekst="Overweging 61: tekst B"),
]


def test_vraagprompt_labelt_elk_fragment_met_ref():
    p = prompt.bouw_vraagprompt("Wat is hoog risico?", CHUNKS)
    assert "[Artikel 6, lid 2]" in p
    assert "tekst A" in p
    assert "Wat is hoog risico?" in p


def test_vind_citaten_alleen_daadwerkelijk_genoemde_refs():
    # Het model kán geen citaat verzinnen: we matchen alleen tegen opgehaalde chunks
    antwoord = "Hoog risico volgt uit [Artikel 6, lid 2]."
    citaten = prompt.vind_citaten(antwoord, CHUNKS)
    assert [c.ref for c in citaten] == ["Artikel 6, lid 2"]


def test_vind_citaten_leeg_bij_abstentie():
    assert prompt.vind_citaten("Dat kan ik niet beantwoorden op basis van mijn bronnen.", CHUNKS) == []


def test_vind_citaten_matcht_verfijnde_ref_op_langste_prefix():
    # Het model verfijnt de ref soms ("…, onder a)"); dat mag de citatie niet laten mislukken
    antwoord = "Dat volgt uit [Artikel 6, lid 2, onder a)]."
    citaten = prompt.vind_citaten(antwoord, CHUNKS)
    assert [c.ref for c in citaten] == ["Artikel 6, lid 2"]


def test_vind_citaten_kiest_langste_prefix_bij_overlappende_refs():
    chunks = [
        NepChunk(ref="Artikel 6", tekst="Artikel 6: tekst A"),
        NepChunk(ref="Artikel 6, lid 2", tekst="Artikel 6, lid 2: tekst B"),
    ]
    antwoord = "Dat volgt uit [Artikel 6, lid 2]."
    citaten = prompt.vind_citaten(antwoord, chunks)
    assert [c.ref for c in citaten] == ["Artikel 6, lid 2"]


def test_systeemprompt_bevat_abstentie_en_geen_advies():
    assert "geen juridisch advies" in prompt.SYSTEEMPROMPT
    assert "jurist" in prompt.SYSTEEMPROMPT


def test_abstentiezin_staat_letterlijk_in_de_systeemprompt():
    # De teller in main.py herkent abstentie aan deze zin. Zou de prompt anders
    # gaan luiden zonder de constante mee te wijzigen, dan telt hij stil niets
    # meer — deze test maakt dat meteen zichtbaar.
    assert prompt.ABSTENTIEZIN in prompt.SYSTEEMPROMPT
