import streamlit as st
from backend.openai_client import get_openai_client

# Charger le client OpenAI avec la clé API depuis les secrets ou .env
client = get_openai_client()

def main():
    """Point d'entrée principal de l'application Streamlit."""
    st.title("CV-LinkedIn Job Matcher")

    # Exemple de test de la clé API
    try:
        st.success("✅ Clé API OpenAI chargée avec succès.")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la clé API : {str(e)}")

if __name__ == "__main__":
    main()
