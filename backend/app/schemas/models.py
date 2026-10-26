"""Contrats de données : toute sortie LLM/OCR est validée par ces schémas."""
from typing import Optional
from pydantic import BaseModel, Field


class DemandeExtraite(BaseModel):
    article: str
    quantite: int = Field(gt=0)
    service: str
    budget: Optional[float] = Field(default=None, ge=0)
    delai: Optional[str] = None


class ChampOCR(BaseModel):
    valeur: str | float | int | None
    confiance: float = Field(ge=0, le=1)


class LigneDocument(BaseModel):
    article: ChampOCR
    quantite: ChampOCR
    prix_unitaire: ChampOCR


class DocumentExtrait(BaseModel):
    fournisseur: ChampOCR
    numero: ChampOCR
    date: ChampOCR
    lignes: list[LigneDocument]
    total: ChampOCR
    tva: ChampOCR

    def confiance_min(self) -> float:
        champs = [self.fournisseur, self.numero, self.date, self.total, self.tva]
        for l in self.lignes:
            champs += [l.article, l.quantite, l.prix_unitaire]
        return min(c.confiance for c in champs)


class Decision(BaseModel):
    decision: str = Field(pattern="^(approbation|refus|correction)$")
    motif: Optional[str] = None
    par: str
