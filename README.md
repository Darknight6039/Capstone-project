# CV-LinkedIn Job Matcher

## Overview

CV-LinkedIn Job Matcher is an AI-powered application designed to help job seekers find relevant job opportunities in Germany by analyzing their resumes and matching them with suitable positions. The application uses a hybrid approach combining traditional matching algorithms with advanced GPT-4o mini capabilities to provide highly accurate job recommendations, skills analysis, and career advice.

- **Resume Analysis**: Upload and parse your CV to extract skills, experience, and education
- **Job Matching**: Find job opportunities that match your profile with detailed compatibility scores
- **Skills Gap Analysis**: Identify matched skills and areas for development
- **Career Insights**: Get personalized career advice and improvement recommendations
- **Multilingual Support**: Search jobs in both English and German

## Technical Architecture

The application uses a hybrid architecture combining:

1. **Traditional Algorithms**: For basic skill and qualification matching
2. **GPT-4o mini API**: For advanced semantic analysis and personalized recommendations
3. **Arbeitnow API Integration**: To source German job listings

## Prerequisites

- Python 3.12
- Streamlit
- OpenAI API key
- Internet connection for job API access

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/cv-linkedin-job-matcher.git
cd cv-linkedin-job-matcher
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Upload your resume (PDF or DOCX format)

3. Navigate to the Job Matches section to search for opportunities:
   - Enter job titles or keywords
   - Select experience level (Entry, Mid, Senior, Executive)
   - Choose language preference (English or German)

4. Explore job matches with compatibility scores

5. Use the Career Insights section for personalized advice

6. Chat with the AI assistant for specific career questions

## Project Structure

```
cv-linkedin-job-matcher/
├── app.py                    # Main application entry point
├── config.py                 # Configuration settings
├── init.py                   # Initialization file
├── requirements.txt          # Dependencies
├── README.md                 # Project documentation
├── backend/                  # Backend logic
│   ├── __init__.py
│   ├── arbeitnow.py          # Job API integration
│   ├── conversation.py       # Chat functionality
│   ├── gpt4o_matcher.py      # GPT-4o integration
│   ├── hybrid_matcher.py     # Combined matching system
│   ├── matcher.py            # Basic matching algorithm
│   ├── openai_client.py      # OpenAI API wrapper
│   ├── openai_resume_extractor.py  # Resume parsing
│   ├── recommender.py        # Recommendation engine
│   └── resume_parser.py      # CV analysis
├── frontend/                 # UI components
│   ├── __init__.py
│   ├── main.py               # Streamlit UI main file
│   └── pages/                # Application pages
├── data/                     # Data storage
├── ModelCV/                  # Machine learning models
└── training/                 # Training components
    ├── CV_Dataset.zip        # Training data
    ├── LeMiel.py             # Model training
    ├── compatibility_predictor.py
    └── skill_extractor.py
```

## Dependencies

The application relies on the following key libraries:
- streamlit==1.32.0
- openai==1.12.0
- python-docx==1.0.1
- PyPDF2==3.0.1
- pandas==2.2.0
- scikit-learn==1.4.0
- python-dotenv==1.0.0
- requests==2.31.0

See `requirements.txt` for the complete list.

## API Integration

The application integrates with:
- **Arbeitnow API**: For sourcing job listings specifically from the German market
- **OpenAI GPT-4o mini API**: For advanced NLP tasks like resume parsing and personalized recommendations

## Future Development

- Implementation of a fine-tuned Phi-3 model to reduce API dependency
- Enhanced multilingual support
- Advanced filtering options
- User profile saving and tracking
- Integration with additional job platforms

## Troubleshooting

If you encounter the "ImportError: cannot import run_streamlit_app from frontend.main" when deploying to Streamlit Cloud:
1. Ensure all `__init__.py` files are present in each directory
2. Modify import statements in app.py to use relative imports
3. Consider simplifying the application structure for deployment

## Credits

Created by Isaia Ebongue, Sebastien Toscano and Rayan Atikossie as part of the Artificial Intelligence for Business Transformation MSc program at SKEMA Business School and ESIEA.
