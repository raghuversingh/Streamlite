import google.generativeai as genai
import streamlit as st
import ml_agent
import database as db

def initialize_gemini(api_key):
    genai.configure(api_key=api_key)
    # Using gemini-2.0-flash which is more stable and widely supported
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        # Fallback to gemini-1.5-pro if gemini-2.0-flash is not available
        model = genai.GenerativeModel('gemini-1.5-pro')
    return model

def get_chat_response(chat_session, user_input, username):
    """
    Enhanced chat response using ML agent for personalization and learning.
    """
    try:
        # Get ML-enhanced prompt
        ml_response = ml_agent.ml_agent.get_adaptive_response(user_input, username)
        
        # Combine ML insights with Gemini for final response
        enhanced_prompt = f"""
        User input: {user_input}
        ML Analysis: {ml_response}
        
        As a therapeutic AI assistant, provide a helpful, empathetic response that incorporates the ML insights.
        Keep the response conversational and supportive.
        """
        
        response = chat_session.send_message(enhanced_prompt)
        final_response = response.text
        
        # Save to database for learning
        db.save_chat_message(username, user_input, final_response)
        
        return final_response
    except Exception as e:
        error_str = str(e)
        # Handle quota exceeded error
        if "429" in error_str or "quota" in error_str.lower():
            return ("⚠️ **API Quota Exceeded**\n\n"
                    "Your Google Generative AI API has reached its quota limit.\n\n"
                    "**Solutions:**\n"
                    "1. Check your billing settings at https://ai.google.dev\n"
                    "2. Upgrade to a paid plan for higher limits\n"
                    "3. Wait for the quota to reset (free tier resets daily)\n"
                    "4. Check usage at https://console.cloud.google.com")
        # Handle other errors
        elif "429" in error_str:
            return ("⚠️ **Rate Limited**\n\nToo many requests. Please wait a moment and try again.")
        else:
            return f"❌ **Error**: {error_str[:200]}"