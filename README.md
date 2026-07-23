# Clarity Hub AI

A sophisticated Streamlit-based AI assistant application that combines Google Gemini AI with machine learning personalization to provide intelligent, empathetic responses. Clarity Hub features user authentication, secure data handling, and adaptive learning capabilities.

## Features

- **AI-Powered Chatbot**: Leverages Google Gemini AI (gemini-2.0-flash) for intelligent, context-aware conversations
- **User Authentication**: Secure login and registration system with password encryption
- **Personalized Responses**: ML agent integration for adaptive, user-specific responses
- **Data Security**: Encryption and security measures to protect user data
- **Database Management**: SQLite-based persistent storage for chat history and user data
- **Admin Panel**: Administrative interface for system management
- **Code Explanation**: Built-in feature to explain code snippets
- **Responsive UI**: Custom CSS styling with modern dark theme design
- **Multi-feature Navigation**: Easy access to CodeGenie, AI Assistant, Code Explainer, and User Profile

## Tech Stack

- **Frontend**: Streamlit
- **AI Model**: Google Generative AI (Gemini 2.0 Flash)
- **Backend**: Python
- **Database**: SQLite3
- **ML Framework**: Transformers, PyTorch, Hugging Face Hub
- **Security**: Cryptography, Passlib, Python-dotenv
- **Data Visualization**: Plotly Express, Pandas

## Project Structure

```
Clarity-Hub_App/
├── app.py                 # Main Streamlit application
├── chatbot.py            # Chatbot logic and Gemini integration
├── auth.py               # Authentication system
├── database.py           # Database operations
├── admin.py              # Admin panel functionality
├── ml_agent.py           # ML personalization and adaptive responses
├── security.py           # Security and encryption utilities
├── style.css             # Custom styling
├── requirements.txt      # Project dependencies
└── tmp_fix_admin*.py     # Temporary admin fixes
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd Clarity-Hub_App
   ```

2. **Create and activate a virtual environment** (optional but recommended)
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**
   - Open `app.py`
   - Replace the placeholder Gemini API key with your actual key:
     ```python
     GEMINI_API_KEY = "YOUR_API_KEY_HERE"
     ```
   - Alternatively, store it in a `.env` file for security

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will open in your default web browser at `http://localhost:8501`

## Usage

### For Users
1. **Register/Login**: Create an account or login with your credentials
2. **Chat with AI**: Interact with the Clarity Hub AI assistant in the main chat interface
3. **Explore Features**: 
   - Use CodeGenie for code-related tasks
   - Access Code Explainer for code analysis
   - View your Profile for personal settings

### For Administrators
- Access the admin panel to manage users and system settings
- Monitor application performance and chat history
- Manage security settings and user permissions

## API Configuration

This application uses Google Gemini AI. To get started:

1. Get your API key from [Google AI Studio](https://aistudio.google.com)
2. Add your key to the application (see Installation section)
3. The app supports both `gemini-2.0-flash` and `gemini-1.5-pro` with automatic fallback

## Security Features

- **Password Encryption**: Secure password hashing using Passlib
- **Data Encryption**: Cryptographic encryption for sensitive data
- **Environment Variables**: Support for `.env` file configuration
- **Secure Sessions**: Session management for authenticated users

## Database

The application uses SQLite for data persistence:
- User account information
- Chat history
- Personalization data
- System logs

Database is automatically initialized on first run.

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web framework |
| google-generativeai | Gemini AI integration |
| pandas | Data processing |
| plotly-express | Data visualization |
| passlib | Password hashing |
| cryptography | Data encryption |
| transformers | NLP models |
| torch | Deep learning framework |
| huggingface_hub | ML model repository |
| python-dotenv | Environment variable management |

## Future Enhancements

- Multi-language support
- Advanced analytics dashboard
- Integration with external APIs
- Mobile application
- Voice interaction capabilities
- Real-time collaboration features

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you have a valid Gemini API key configured
- Verify Python version is 3.8 or higher

### Database errors
- Delete `database.db` (if it exists) and restart the app to reinitialize
- Check file permissions in the project directory

### API key issues
- Verify your API key is valid and active
- Check Google AI Studio for any quota limitations
- Ensure the API key has the necessary permissions enabled

## Contributing

To contribute to this project:
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is provided as-is for educational and personal use.

## Support

For issues, questions, or suggestions, please create an issue in the project repository.

## Disclaimer

This application uses AI models that may generate responses based on training data. Users should verify critical information independently. The application is designed for informational purposes and should not replace professional medical or counseling services.

---

**Last Updated**: July 2026
