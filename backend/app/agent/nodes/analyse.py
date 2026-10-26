from typing import Optional
from pydantic import BaseModel, Field, ValidationError
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.agent.audit import etape
from app.agent import tools
from app.config import settings
from app.schemas.models import DemandeExtraite


class ExtractionDemande(BaseModel):
    demande: Optional[DemandeExtraite] = Field(
        default=None,
        description="Détails extraits de la demande si suffisamment clairs et conformes au schéma DemandeExtraite",
    )
    infos_suffisantes: bool = Field(
        description="True si au moins l'article, la quantité (> 0) et le service demandeur sont identifiés avec certitude. False si une information essentielle manque ou est trop vague.",
    )
    question_demandeur: Optional[str] = Field(
        default=None,
        description="Si la demande est incomplète (infos_suffisantes=False), rédiger ici une question polie, directe et précise destinée au demandeur pour clarifier les éléments manquants (article, quantité, service, budget, etc.). Null si la demande est complète.",
    )
    raison: str = Field(
        description="Brève justification de l'analyse pour le journal d'audit",
    )


PROMPT_COMPRENDRE = ChatPromptTemplate.from_messages([
    (
        "system",
        "Tu es un assistant expert des achats en entreprise.\n"
        "Ton rôle est d'analyser la demande brute d'un collaborateur et d'en extraire les informations clés selon le schéma DemandeExtraite :\n"
        "- article : désignation claire et précise du produit ou service demandé (ex: 'écran 27 pouces')\n"
        "- quantite : nombre d'unités demandées (entier strictement supérieur à 0, fixé à 1 si l'article est au singulier sans précision explicite)\n"
        "- service : nom du département ou service demandeur (ex: 'Design', 'IT', 'RH', 'Finance', 'Marketing', etc.)\n"
        "- budget : montant indicatif en euros mentionné par le demandeur (flottant >= 0, ou null si non précisé)\n"
        "- delai : délai ou date souhaitée si mentionné (ou null si non précisé)\n\n"
        "Règles d'évaluation :\n"
        "1. Si la demande ne permet pas d'identifier clairement l'article, la quantité (> 0) ET le service demandeur, ou si elle est incompréhensible/trop vague (ex: 'bonjour', 'x', 'besoin de matériel') :\n"
        "   - Définis infos_suffisantes = False\n"
        "   - Définis demande = null\n"
        "   - Rédige dans question_demandeur une question courtoise, explicite et ciblée demandant précisément les éléments manquants nécessaires pour traiter son achat.\n"
        "   - Résume le problème dans raison.\n"
        "2. Si les informations obligatoires sont présentes :\n"
        "   - Définis infos_suffisantes = True\n"
        "   - Définis question_demandeur = null\n"
        "   - Remplis l'objet demande selon le schéma DemandeExtraite et fournis un court résumé dans raison.",
    ),
    ("user", "{input}"),
])


def extraire_demande_llm(texte: str) -> tuple[Optional[DemandeExtraite], bool, Optional[str], str]:
    """Extrait et valide une demande d'achat brute à l'aide d'un LLM et du schéma Pydantic DemandeExtraite.

    Retourne :
        (demande_validee: Optional[DemandeExtraite], infos_suffisantes: bool, question_demandeur: Optional[str], raison: str)
    """
    texte = (texte or "").strip()
    if not texte:
        return (
            None,
            False,
            "Votre demande d'achat est vide. Pouvez-vous préciser l'article souhaité, la quantité et votre service demandeur ?",
            "Demande vide : précisions demandées",
        )

    if not settings.llm_api_key:
        return (
            None,
            False,
            "Impossible d'analyser la demande (clé LLM non configurée). Merci de contacter l'administrateur.",
            "Clé LLM_API_KEY non configurée",
        )

    try:
        llm = ChatGroq(
            api_key=settings.llm_api_key,
            model=settings.llm_model or "openai/gpt-oss-120b",
            temperature=0,
        )
        chain = PROMPT_COMPRENDRE | llm.with_structured_output(ExtractionDemande)
        resultat: ExtractionDemande = chain.invoke({"input": texte})

        if resultat.infos_suffisantes and resultat.demande:
            demande_validee = DemandeExtraite.model_validate(resultat.demande)
            return (
                demande_validee,
                True,
                None,
                resultat.raison or "Extraction de la demande validée par Pydantic",
            )
        else:
            question = (
                resultat.question_demandeur
                or "Pouvez-vous préciser l'article souhaité, la quantité ainsi que votre département demandeur ?"
            )
            return (
                None,
                False,
                question,
                resultat.raison or "Informations insuffisantes pour traiter la demande",
            )
    except ValidationError as ve:
        return (
            None,
            False,
            "Certains paramètres de votre demande sont invalides (quantité ou budget incorrects). Pouvez-vous préciser votre besoin ?",
            f"Erreur de validation Pydantic DemandeExtraite : {ve}",
        )
    except Exception as e:
        return (
            None,
            False,
            "Une erreur technique est survenue lors de l'analyse de votre demande. Pouvez-vous reformuler votre besoin ?",
            f"Erreur lors de l'extraction LLM : {e}",
        )


@etape("reception")
def reception(s):
    return {"statut": "recue", "_raison": "Demande reçue"}


@etape("comprendre")
def comprendre(s):
    texte = s.get("demande_brute", "")
    demande_validee, infos_suffisantes, question_demandeur, raison = extraire_demande_llm(texte)

    if infos_suffisantes and demande_validee:
        return {
            "demande": demande_validee.model_dump(),
            "infos_suffisantes": True,
            "question_demandeur": None,
            "_raison": raison,
        }
    else:
        return {
            "demande": {},
            "infos_suffisantes": False,
            "statut": "incomplet",
            "question_demandeur": question_demandeur,
            "_raison": f"Demande incomplète : {raison}",
        }


@etape("attente_precisions")
def attente_precisions(s):
    question = s.get("question_demandeur") or "Précisions nécessaires sur la demande"
    tools.notifier("demandeur", f"Précisions requises : {question}")
    return {
        "statut": "incomplet",
        "_raison": f"Question posée au demandeur : {question}",
    }


@etape("extraire_document")
def extraire_document(s):
    # TODO: tools.analyser_document(...) -> DocumentExtrait + confiance par champ
    return {"document": {"confiance_min": 0.95}, "_raison": "Texte natif ou OCR + extraction structurée"}


@etape("verifier_ocr")
def verifier_ocr(s):
    conf = (s.get("document") or {}).get("confiance_min", 0.0)
    ok = conf >= settings.seuil_confiance_ocr
    return {"ocr_fiable": ok, "_raison": f"confiance min {conf} / seuil {settings.seuil_confiance_ocr}"}


@etape("attente_correction_ocr")
def attente_correction_ocr(s):
    return {"statut": "correction_ocr", "_raison": "Correction humaine des champs extraits"}
