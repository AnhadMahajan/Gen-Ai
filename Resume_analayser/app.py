import os
import streamlit as st
import time
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ GOOGLE_API_KEY not found in environment variables!")
        st.stop()
    genai.configure(api_key=api_key)
    logger.info("✅ Google API configured successfully")
except Exception as e:
    st.error(f"❌ Failed to configure Google API: {e}")
    st.stop()

st.set_page_config(
    page_title="AI Resume Analyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;

    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    .feature-card {
        background: grey;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: #C9D1D9;
        padding: 1.5rem;
        border-radius: 12px;
        color: #0D1117;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        animation: fadeInUp 0.6s ease-out;
    }
    
    .analysis-section {
        background: #161B22;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    .error-card {
        background: grey;
        border: 1px solid #fed7d7;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        color: #c53030;
    }
    
    .success-card {
        background: grey;
        border: 1px solid #9ae6b4;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        color: #22543d;
    }
    
    .debug-section {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.9em;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🚀 AI Resume Analyzer Pro</h1>
    <p>Transform your career with AI-powered resume analysis and insights</p>
</div>
""", unsafe_allow_html=True)

if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

with st.sidebar:
    st.markdown("### 🛠️ Settings")
    debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
    st.session_state.debug_mode = debug_mode
    
    st.markdown("---")
    
    st.markdown("""
    <div class="sidebar-content">
        <h3>🎯 Features</h3>
        <ul style="list-style-type: none; padding: 0;">
            <li>📊 Comprehensive Resume Analysis</li>
            <li>🎯 Job Match Scoring</li>
            <li>💡 Skill Gap Analysis</li>
            <li>📈 ATS Compatibility Check</li>
            <li>🎨 Visual Skills Breakdown</li>
            <li>📚 Course Recommendations</li>
            <li>🏆 Industry Benchmarking</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.analysis_history:
        st.markdown("### 📋 Analysis History")
        for i, analysis in enumerate(st.session_state.analysis_history[-3:]):
            with st.expander(f"Analysis {len(st.session_state.analysis_history) - i}"):
                st.write(f"**Date:** {analysis['timestamp']}")
                st.write(f"**Score:** {analysis.get('score', 'N/A')}/100")

def extract_text_from_pdf(pdf_path):
    """Enhanced PDF text extraction with better error handling"""
    text = ""
    extraction_methods = []
    
    try:

        logger.info("Attempting direct text extraction...")
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text.strip():
            extraction_methods.append("Direct text extraction")
            logger.info(f"✅ Direct extraction successful. Length: {len(text)}")
            if st.session_state.debug_mode:
                st.success(f"✅ Direct text extraction successful ({len(text)} characters)")
            return text.strip(), extraction_methods
        else:
            logger.warning("Direct text extraction returned empty result")
            
    except Exception as e:
        logger.error(f"Direct text extraction failed: {e}")
        if st.session_state.debug_mode:
            st.warning(f"Direct extraction failed: {e}")

    try:

        logger.info("Attempting OCR extraction...")
        images = convert_from_path(pdf_path, dpi=300)  
        ocr_text = ""
        
        for i, image in enumerate(images):

            image = image.convert('L')  
            page_text = pytesseract.image_to_string(image, config='--psm 6')
            ocr_text += page_text + "\n"
            
        if ocr_text.strip():
            extraction_methods.append("OCR extraction")
            logger.info(f"✅ OCR extraction successful. Length: {len(ocr_text)}")
            if st.session_state.debug_mode:
                st.success(f"✅ OCR extraction successful ({len(ocr_text)} characters)")
            return ocr_text.strip(), extraction_methods
            
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        if st.session_state.debug_mode:
            st.error(f"OCR extraction failed: {e}")

    return "", extraction_methods

def validate_resume_text(text):
    """Validate extracted resume text"""
    if not text or len(text.strip()) < 50:
        return False, "Resume text is too short (less than 50 characters)"
    

    common_keywords = ['experience', 'education', 'skills', 'work', 'job', 'project', 'university', 'college', 'degree']
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in common_keywords if keyword in text_lower)
    
    if keyword_count < 2:
        return False, "Text doesn't appear to be a resume (missing common resume keywords)"
    
    return True, "Resume text validation passed"

def analyze_resume_enhanced(resume_text, job_description=None):
    """Enhanced resume analysis with improved error handling"""
    if not resume_text:
        return {"error": "Resume text is required for analysis."}
    

    is_valid, validation_message = validate_resume_text(resume_text)
    if not is_valid:
        return {"error": f"Resume validation failed: {validation_message}"}
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        

        enhanced_prompt = f"""
        You are an expert HR professional and career coach with deep expertise across multiple domains including Data Science, AI/ML, Software Development, DevOps, Marketing, and Human Resources.
        
        Analyze the following resume comprehensively and provide a structured evaluation in JSON format:
        
        Resume Text:
        {resume_text[:4000]}  # Limit text to avoid token limits
        
        {"Job Description: " + job_description[:1000] if job_description else ""}
        
        Please provide your analysis in the following JSON structure (ensure all values are properly formatted):
        {{
            "overall_score": 75,
            "strengths": ["Strong technical skills", "Good educational background", "Relevant work experience"],
            "weaknesses": ["Missing soft skills", "Could improve formatting", "Needs more quantified achievements"],
            "skills_present": ["Python", "Java", "SQL", "Machine Learning"],
            "skills_missing": ["Docker", "Kubernetes", "AWS", "React"],
            "ats_score": 82,
            "experience_level": "Mid",
            "recommended_courses": ["Advanced Python Programming", "Cloud Computing Fundamentals", "Data Structures and Algorithms"],
            "industry_fit": ["Technology", "Data Science", "Software Development"],
            "salary_estimate": "$60,000 - $80,000",
            "job_match_score": {85 if job_description else 0},
            "recommendations": ["Add more quantified achievements", "Include soft skills", "Improve ATS compatibility"]
        }}
        
        Important: Respond ONLY with valid JSON. Do not include any additional text or explanations outside the JSON structure.
        """

        logger.info("Sending request to Gemini API...")
        response = model.generate_content(enhanced_prompt)
        response_text = response.text.strip()
        
        if st.session_state.debug_mode:
            st.markdown("### 🔍 Debug: Raw AI Response")
            st.text_area("Raw Response", response_text, height=200)
        

        response_text = response_text.replace('```json', '').replace('```', '').strip()
        

        try:
            analysis_result = json.loads(response_text)
            logger.info("✅ JSON parsing successful")
            return analysis_result
        except json.JSONDecodeError as je:
            logger.error(f"JSON parsing failed: {je}")

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis_result = json.loads(json_match.group())
                    logger.info("✅ JSON extraction and parsing successful")
                    return analysis_result
                except:
                    pass
            
            return {"error": f"Could not parse AI response as JSON: {je}", "raw_text": response_text}
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Analysis failed: {str(e)}", "traceback": traceback.format_exc()}

def create_skills_chart(skills):
    """Create skills visualization chart"""
    if not skills:
        return None
    

    skills = skills[:15]
    df = pd.DataFrame({'Skills': skills, 'Count': [1] * len(skills)})
    fig = px.bar(df, x='Skills', y='Count', 
                 title="Skills Identified in Resume",
                 color='Count',
                 color_continuous_scale='viridis')
    fig.update_layout(
        showlegend=False,
        xaxis_tickangle=-45,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_score_gauge(score, title):
    """Create score gauge visualization"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig


col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📄 Upload Resume</h3>
        <p>Upload your resume in PDF format for comprehensive analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=["pdf"],
        help="Upload a PDF file of your resume"
    )

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>💼 Job Description (Optional)</h3>
        <p>Add a job description to get targeted matching insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    job_description = st.text_area(
        "Enter Job Description",
        height=150,
        placeholder="Paste the job description here to get personalized matching analysis..."
    )


if uploaded_file is not None:
    st.markdown("""
    <div class="success-card">
        <h4>✅ Resume uploaded successfully!</h4>
        <p>File: {}</p>
        <p>Size: {:.2f} KB</p>
    </div>
    """.format(uploaded_file.name, len(uploaded_file.getvalue()) / 1024), unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="error-card">
        <h4>⚠️ Please upload your resume</h4>
        <p>PDF format required for analysis</p>
    </div>
    """, unsafe_allow_html=True)


if uploaded_file:

    with open("uploaded_resume.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if st.button("🚀 Analyze Resume", type="primary"):

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:

            status_text.text("📄 Extracting text from PDF...")
            progress_bar.progress(25)
            
            resume_text, extraction_methods = extract_text_from_pdf("uploaded_resume.pdf")
            st.session_state.resume_text = resume_text
            
            if st.session_state.debug_mode:
                st.markdown("### 🔍 Debug: Text Extraction")
                st.write(f"**Extraction methods used:** {', '.join(extraction_methods)}")
                st.write(f"**Text length:** {len(resume_text)} characters")
                st.text_area("Extracted Text (first 500 chars)", resume_text[:500], height=150)
            
            if not resume_text:
                st.error("❌ Failed to extract text from PDF. Please ensure your PDF contains readable text.")
                st.stop()
            

            status_text.text("🤖 Analyzing with AI...")
            progress_bar.progress(50)
            
            analysis = analyze_resume_enhanced(resume_text, job_description)
            

            status_text.text("📊 Creating visualizations...")
            progress_bar.progress(75)
            time.sleep(0.5)
            

            status_text.text("✅ Analysis complete!")
            progress_bar.progress(100)
            time.sleep(0.5)
            

            progress_bar.empty()
            status_text.empty()
            

            if "error" not in analysis:
                st.session_state.analysis_complete = True
                

                st.session_state.analysis_history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'score': analysis.get('overall_score', 0),
                    'analysis': analysis
                })
                

                st.markdown("## 📊 Analysis Results")
                

                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{analysis.get('overall_score', 0)}/100</h3>
                        <p>Overall Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{analysis.get('ats_score', 0)}/100</h3>
                        <p>ATS Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{analysis.get('experience_level', 'Unknown')}</h3>
                        <p>Experience Level</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    score = analysis.get('job_match_score', 0) if job_description else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{score}/100</h3>
                        <p>Job Match</p>
                    </div>
                    """, unsafe_allow_html=True)
                

                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>💪 Strengths</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for strength in analysis.get('strengths', []):
                        st.write(f"✅ {strength}")
                    
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>🎯 Skills Present</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    skills_present = analysis.get('skills_present', [])
                    if skills_present:
                        skills_text = ", ".join(skills_present)
                        st.write(skills_text)
                        

                        fig = create_skills_chart(skills_present)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>🔧 Areas for Improvement</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for weakness in analysis.get('weaknesses', []):
                        st.write(f"🔄 {weakness}")
                    
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>📚 Recommended Skills</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for skill in analysis.get('skills_missing', []):
                        st.write(f"➕ {skill}")
                

                st.markdown("## 📈 Score Breakdown")
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = create_score_gauge(analysis.get('overall_score', 0), "Overall Score")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    fig2 = create_score_gauge(analysis.get('ats_score', 0), "ATS Compatibility")
                    st.plotly_chart(fig2, use_container_width=True)
                

                st.markdown("""
                <div class="analysis-section">
                    <h3>💡 Recommendations</h3>
                </div>
                """, unsafe_allow_html=True)
                
                for rec in analysis.get('recommendations', []):
                    st.write(f"🎯 {rec}")
                

                st.markdown("""
                <div class="analysis-section">
                    <h3>📚 Recommended Courses</h3>
                </div>
                """, unsafe_allow_html=True)
                
                for course in analysis.get('recommended_courses', []):
                    st.write(f"📖 {course}")
                

                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>🏭 Industry Fit</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for industry in analysis.get('industry_fit', []):
                        st.write(f"🏢 {industry}")
                
                with col2:
                    st.markdown("""
                    <div class="analysis-section">
                        <h3>💰 Salary Estimate</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    salary = analysis.get('salary_estimate', 'Not available')
                    st.write(f"💵 {salary}")
            
            else:

                st.error("❌ Analysis failed. Please see details below:")
                
                error_msg = analysis.get('error', 'Unknown error')
                st.markdown(f"""
                <div class="error-card">
                    <h4>Error Details:</h4>
                    <p>{error_msg}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if 'raw_text' in analysis:
                    with st.expander("🔍 Raw AI Response"):
                        st.text(analysis['raw_text'])
                
                if st.session_state.debug_mode and 'traceback' in analysis:
                    with st.expander("🐛 Technical Details"):
                        st.text(analysis['traceback'])
        
        except Exception as e:
            st.error(f"❌ Unexpected error occurred: {str(e)}")
            if st.session_state.debug_mode:
                st.text(traceback.format_exc())

