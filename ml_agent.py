from transformers import pipeline
import pandas as pd
import random
import sqlite3
import database as db

# This version avoids torch/stable-baselines3 so the app runs in small environments.

class MLAgent:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

    def analyze_user_history(self, username):
        conn = sqlite3.connect('clarity_hub.db')
        mood_df = pd.read_sql_query(
            "SELECT date, score FROM mood_logs WHERE username=? ORDER BY date",
            conn,
            params=(username,),
        )
        conn.close()
        journals = db.get_user_journals(username, limit=10)

        insights = {
            'avg_mood': 3.0,
            'mood_trend': 'stable',
            'avg_sentiment': 0.5,
            'recommendations': [],
        }

        if not mood_df.empty:
            insights['avg_mood'] = float(mood_df['score'].mean())
            insights['mood_trend'] = (
                'improving' if mood_df['score'].iloc[-1] > mood_df['score'].iloc[0] else 'declining'
            )

        if not journals.empty:
            journals['entry_text'] = journals['entry_text'].astype(str)
            sentiments = [self.sentiment_analyzer(text)[0] for text in journals['entry_text']]
            positive_scores = [s['score'] for s in sentiments if s['label'] in ['LABEL_2', 'POSITIVE', '5 stars']]
            insights['avg_sentiment'] = float(sum(positive_scores) / len(positive_scores)) if positive_scores else 0.5

        if insights['avg_mood'] <= 2 or insights['avg_sentiment'] <= 0.4:
            insights['recommendations'] = [
                'Try a short breathing exercise or a five-minute walk.',
                'Write down one positive thing you noticed today.',
                'If you are feeling overwhelmed, reach out to a trusted friend or counselor.',
            ]
        elif insights['avg_mood'] >= 4 and insights['avg_sentiment'] >= 0.7:
            insights['recommendations'] = [
                'Keep celebrating the small wins and mark them in your journal.',
                'Maintain the habits that are making you feel good.',
                'Consider sharing your progress with someone who supports you.',
            ]
        else:
            insights['recommendations'] = [
                'Try a short grounding exercise and notice how your body feels.',
                'Take a moment to reflect on one thing you appreciate today.',
                'If you’d like, express how you are feeling in your next journal entry.',
            ]

        return insights

    def detect_risk(self, username):
        insights = self.analyze_user_history(username)
        mood = insights.get('avg_mood', 3.0)
        sentiment = insights.get('avg_sentiment', 0.5)

        if mood <= 2 and sentiment <= 0.4:
            return {
                'risk': True,
                'level': 'High',
                'reason': 'Combined low mood and negative sentiment indicate elevated emotional risk.'
            }
        if mood <= 2 or sentiment <= 0.4:
            return {
                'risk': True,
                'level': 'Moderate',
                'reason': 'There are signs of stress or sadness that may need extra attention.'
            }
        return {
            'risk': False,
            'level': 'Low',
            'reason': 'Mood and sentiment are in a stable range.'
        }

    def get_recommendations(self, username):
        insights = self.analyze_user_history(username)
        return insights.get('recommendations', [])

    def generate_personalized_question(self, username, context=""):
        insights = self.analyze_user_history(username)
        mood = insights.get('avg_mood', 3.0)
        sentiment = insights.get('avg_sentiment', 0.5)

        if mood <= 2 or sentiment <= 0.4:
            choices = [
                "I care about you. What is one thing that would make today feel better?",
                "Can you share a small win from the last 24 hours?",
                "What feels hardest right now, and what would help if it were a little easier?",
            ]
        elif mood >= 4 and sentiment >= 0.7:
            choices = [
                "That's wonderful—what kept your spirits up recently?",
                "What positive habits have you noticed building lately?",
                "How can we continue this momentum in the coming days?",
            ]
        else:
            choices = [
                "How would you describe your emotional energy right now?",
                "Is there something on your mind that you want to talk through?",
                "What is one thing you can do today for yourself?",
            ]

        return random.choice(choices)

    def get_adaptive_response(self, user_input, username):
        sentiment = self.sentiment_analyzer(user_input)[0]
        risk = self.detect_risk(username)
        recommendations = self.get_recommendations(username)

        if sentiment['label'] in ['NEGATIVE', 'LABEL_0']:
            question = self.generate_personalized_question(username, "negative")
            return (
                f"I’m sorry you’re feeling this way. {question}\n\n"
                f"**Risk Level:** {risk['level']} — {risk['reason']}\n"
                f"**Suggestion:** {recommendations[0] if recommendations else 'Take a moment to focus on your breathing.'}"
            )

        if sentiment['label'] in ['POSITIVE', 'LABEL_2']:
            return (
                "It sounds like you’re doing well emotionally right now — that’s fantastic to hear. Keep celebrating your wins.\n\n"
                f"**Suggestion:** {recommendations[0] if recommendations else 'Keep up the good work and continue tracking what feels positive.'}"
            )

        question = self.generate_personalized_question(username, "neutral")
        return (
            f"Thanks for sharing. {question}\n\n"
            f"**Suggestion:** {recommendations[0] if recommendations else 'Notice how you feel and check in with yourself again soon.'}"
        )

ml_agent = MLAgent()