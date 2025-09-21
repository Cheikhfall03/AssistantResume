import chainlit as cl
from dotenv import load_dotenv
from groq import AsyncGroq # Utilisation du client asynchrone
import json
import os
import requests
from pypdf import PdfReader

# --- LOGIQUE BACKEND (LÉGÈREMENT ADAPTÉE POUR L'ASYNCHRONE) ---

# Charger les variables d'environnement
load_dotenv(override=True)

# Les fonctions de "tool" (outils) restent synchrones car elles font des I/O simples
def push(text):
    """Envoie une notification via Pushover."""
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            }
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification Pushover : {e}")

def record_user_details(email, name="Nom non fourni", number="Numéro non fourni", location="Lieu non fourni", notes="non fournies"):
    """Enregistre les détails d'un contact intéressé et envoie une notification."""
    push(f"🔔 CONTACT INTÉRESSÉ: {name} - Email: {email} - Tél: {number} - Lieu: {location} - Notes: {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    """Enregistre une question à laquelle le bot n'a pas pu répondre et envoie une notification."""
    push(f"❓ QUESTION SANS RÉPONSE: {question}")
    return {"recorded": "ok"}

def record_project_opportunity(details, contact_info=""):
    """Enregistre une opportunité de projet pour suivi."""
    print(f"Opportunité enregistrée: {details} - Contact: {contact_info}")
    return {"recorded": "ok"}

# Définitions JSON des outils pour l'API LLM (inchangées)
record_user_details_json = {
    "name": "record_user_details", "description": "Utilisez cet outil pour enregistrer les coordonnées lorsqu'un utilisateur fournit son adresse e-mail et manifeste un réel intérêt commercial. Cela enverra une notification.", "parameters": {"type": "object", "properties": {"email": {"type": "string", "description": "L'adresse e-mail de cet utilisateur (OBLIGATOIRE)"}, "name": {"type": "string", "description": "Le nom de l'utilisateur, s'il l'a fourni"}, "number": {"type": "string", "description": "Le numéro de téléphone de l'utilisateur, s'il l'a fourni"}, "location": {"type": "string", "description": "La localisation de l'utilisateur, si elle est fournie"}, "notes": {"type": "string", "description": "Contexte de son intérêt : détails du projet, opportunité d'emploi, type de collaboration, etc."}}, "required": ["email"], "additionalProperties": False}
}
record_unknown_question_json = {
    "name": "record_unknown_question", "description": "Utilisez cet outil UNIQUEMENT lorsque vous ne pouvez pas répondre à une question sur le parcours professionnel, les compétences ou l'expérience de Cheikh FALL que l'on pourrait raisonnablement s'attendre à ce que vous connaissiez", "parameters": {"type": "object", "properties": {"question": {"type": "string", "description": "La question professionnelle à laquelle il n'a pas été possible de répondre"}}, "required": ["question"], "additionalProperties": False}
}
record_project_opportunity_json = {
    "name": "record_project_opportunity", "description": "Utilisez cet outil UNIQUEMENT pour enregistrer des opportunités de projet/emploi lorsque les coordonnées ne sont pas encore fournies, afin de suivre l'intérêt sans notification", "parameters": {"type": "object", "properties": {"details": {"type": "string", "description": "Détails sur le projet, l'offre d'emploi ou l'opportunité commerciale"}, "contact_info": {"type": "string", "description": "Toute information de contact si fournie"}}, "required": ["details"], "additionalProperties": False}
}
tools = [{"type": "function", "function": record_user_details_json}, {"type": "function", "function": record_unknown_question_json}, {"type": "function", "function": record_project_opportunity_json}]

class Me:
    def __init__(self):
        self.groq = AsyncGroq() # Client asynchrone
        self.name = "Cheikh FALL"
        try:
            reader = PdfReader("Profile.pdf")
            cv_reader = PdfReader("Cheikh_FALL_CV_EN_VF.pdf")
            self.linkedin = ""
            for page in reader.pages: self.linkedin += page.extract_text() or ""
            for page in cv_reader.pages: self.linkedin += page.extract_text() or ""
            with open("summary.txt", "r", encoding="utf-8") as f: self.summary = f.read()
        except FileNotFoundError as e:
            # En Chainlit, les erreurs de démarrage s'affichent dans la console
            print(f"ERREUR: Fichier de profil manquant, certaines informations peuvent ne pas être disponibles: {e.filename}")
            self.linkedin, self.summary = "Profil non disponible", "Résumé non disponible"

    def handle_tool_call(self, tool_calls):
        """Exécute les appels aux fonctions demandés par le modèle."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            # Utilise globals() pour trouver la fonction Python par son nom
            tool_function = globals().get(tool_name)
            if tool_function:
                result = tool_function(**arguments)
            else:
                result = {"error": f"Tool '{tool_name}' not found."}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        """Génère le prompt système avec le contexte."""
        return f"""Vous agissez en tant que {self.name}. Vous répondez aux questions sur le site web de {self.name}, en particulier celles liées à sa carrière, son parcours, ses compétences et son expérience. Votre responsabilité est de représenter {self.name} de la manière la plus fidèle possible. Vous disposez d'un résumé du parcours et du profil LinkedIn de {self.name} pour répondre aux questions. Soyez professionnel et engageant, comme si vous parliez à un client potentiel ou un futur employeur.
        RÈGLES DE NOTIFICATION IMPORTANTES :
        - N'envoyez pas de notifications pour des questions générales ou des bavardages.
        - Utilisez 'record_unknown_question' UNIQUEMENT pour les questions sur le parcours professionnel de {self.name} auxquelles vous ne pouvez vraiment pas répondre avec les informations fournies.
        - Utilisez 'record_project_opportunity' quand quelqu'un mentionne : offres d'emploi, propositions de projet, intérêt pour un recrutement, opportunités de collaboration, ou des demandes commerciales sérieuses - MAIS demandez leurs coordonnées avant d'utiliser cet outil.
        - Utilisez 'record_user_details' UNIQUEMENT quand quelqu'un fournit réellement ses informations de contact (l'email est requis). Cet outil envoie une notification, donc utilisez-le seulement quand vous avez de vraies coordonnées.
        - N'UTILISEZ PAS les outils pour des conversations générales, du bavardage, ou des questions non liées aux affaires professionnelles.
        - Répondez aux questions générales sur la technologie, la programmation ou l'industrie en utilisant vos connaissances sans déclencher de notifications.
        PROCESSUS POUR LES CONTACTS INTÉRESSÉS :
        1. Quand quelqu'un mentionne un intérêt commercial ou des opportunités, engagez la conversation de manière professionnelle et demandez ses coordonnées.
        2. Utilisez 'record_user_details' seulement lorsqu'ils fournissent une adresse e-mail.
        3. Si la personne mentionne un projet/opportunité mais ne fournit pas d'informations de contact, encouragez-la à partager son email pour un suivi.
        ## Résumé :
        {self.summary}
        ## Profil LinkedIn :
        {self.linkedin}
        Avec ce contexte, veuillez discuter avec l'utilisateur, en restant toujours dans le personnage de {self.name}."""
    
    async def chat(self, message_content, history):
        """Logique principale du chat, maintenant asynchrone."""
        # L'historique est une simple liste de dictionnaires
        history = [{"role": h["role"], "content": h["content"]} for h in history]

        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message_content}]
        
        done = False
        while not done:
            try:
                # Appel asynchrone à l'API Groq
                response = await self.groq.chat.completions.create(model="gemma2-9b-it", messages=messages, tools=tools, tool_choice="auto")
                message_response = response.choices[0].message
                
                if message_response.tool_calls:
                    # Si le modèle veut appeler un outil, on le gère
                    results = self.handle_tool_call(message_response.tool_calls)
                    messages.extend([message_response] + results)
                else:
                    # Sinon, la conversation est terminée pour ce tour
                    done = True
            except Exception as e:
                print(f"Erreur API: {str(e)}")
                return "Désolé, je rencontre un problème technique. Veuillez réessayer."
                
        return response.choices[0].message.content

# --- INTERFACE CHAINLIT ---

@cl.on_chat_start
async def start_chat():
    """Fonction d'initialisation au début d'une nouvelle session de chat."""
    # Instancier la classe Me et la sauvegarder dans la session utilisateur
    cl.user_session.set("me", Me())
    # Initialiser l'historique de la conversation
    cl.user_session.set("history", [])
    
    # Envoyer le message de bienvenue
    await cl.Message(
    author="Assistant IA",
    content=(
        "👋 Bienvenue ! Je suis l’assistant IA de **Cheikh FALL**.\n\n"
        "Vous pouvez me poser toutes vos questions sur son **parcours professionnel**, ses **compétences techniques**, ou ses **expériences passées**.\n\n"
        "💼 Vous avez une **opportunité d’embauche**, un **projet à proposer** ou une **idée de collaboration** ? N’hésitez pas à m’en parler ici, je suis là pour faciliter l’échange !"
    )
).send()


@cl.on_message
async def main(message: cl.Message):
    """Fonction appelée à chaque fois que l'utilisateur envoie un message."""
    # Récupérer l'instance et l'historique depuis la session
    me_instance = cl.user_session.get("me")
    history = cl.user_session.get("history")
    
    # Afficher un indicateur de chargement
    msg = cl.Message(content="")
    await msg.send()
    
    # Appeler la logique du chat
    response_content = await me_instance.chat(message.content, history)
    
    # Mettre à jour le message vide avec la réponse finale
    msg.content = response_content
    await msg.update()
    
    # Mettre à jour l'historique dans la session
    history.append({"role": "user", "content": message.content})
    history.append({"role": "assistant", "content": response_content})
    cl.user_session.set("history", history)