from typing import Literal, Optional, TypedDict


class EtatAgent(TypedDict, total=False):
    demande_id: str
    demande_brute: str
    pieces_jointes: list[str]
    demande: dict                    # DemandeExtraite
    infos_suffisantes: bool
    document: Optional[dict]         # DocumentExtrait
    ocr_fiable: bool
    fournisseurs: list[dict]
    budget_ok: bool
    violations: list[str]
    ecarts: list[str]
    controles_ok: bool
    regularisable: bool
    decision: Optional[Literal["approbation", "refus", "correction"]]
    motif: Optional[str]
    commande_id: Optional[str]
    statut: str
    journal: list[dict]              # audit : étape, raison, horodatage
    nb_etapes: int                   # compteur anti-boucle
