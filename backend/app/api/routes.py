import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.agent.graph import construire
from app.config import settings

router = APIRouter()
graph = construire()  # TODO: PostgresSaver pour persister les threads
UPLOADS = settings.uploads_dir
# Garde-fou : l'humain ne peut modifier que ces clés de l'état
CLES_HUMAINES = {"decision", "motif", "demande_brute", "document", "ocr_fiable", "regularisable"}


class NouvelleDemande(BaseModel):
    texte: str
    pieces_jointes: list[str] = []


class Reprise(BaseModel):
    champs: dict = {}


def _vue(thread_id: str):
    st = graph.get_state({"configurable": {"thread_id": thread_id}})
    if not st.values:
        raise HTTPException(404, "Demande inconnue")
    return {"id": thread_id, "etat": st.values, "en_attente": list(st.next)}


@router.post("/documents")
async def deposer(fichier: UploadFile):
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / f"{uuid.uuid4().hex}_{Path(fichier.filename).name}"
    with dest.open("wb") as f:
        shutil.copyfileobj(fichier.file, f)
    return {"chemin": str(dest)}


@router.post("/demandes")
def creer(d: NouvelleDemande):
    tid = str(uuid.uuid4())
    graph.invoke({"demande_id": tid, "demande_brute": d.texte, "pieces_jointes": d.pieces_jointes},
                 {"configurable": {"thread_id": tid}})
    return _vue(tid)


@router.get("/demandes/{tid}")
def lire(tid: str):
    return _vue(tid)


@router.post("/demandes/{tid}/reprendre")
def reprendre(tid: str, r: Reprise):
    interdit = set(r.champs) - CLES_HUMAINES
    if interdit:
        raise HTTPException(400, f"Clés non modifiables : {sorted(interdit)}")
    cfg = {"configurable": {"thread_id": tid}}
    if r.champs:
        graph.update_state(cfg, r.champs)
    graph.invoke(None, cfg)
    return _vue(tid)
