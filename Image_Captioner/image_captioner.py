import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import os
from typing import Optional, List

st.set_page_config(
    page_title="VisionCraft - AI-Powered Multimodal Image Analysis & Caption Generation",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .result-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    
    .tag {
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ImageCaptioner:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_detailed_caption(self, image: Image.Image) -> str:
        prompt = """
        Analyze this image and provide a detailed, comprehensive description. 
        Include information about:
        - Main subjects and objects
        - Setting and environment
        - Colors, lighting, and mood
        - Actions or activities happening
        - Style or artistic elements
        - Any text visible in the image
        
        Write in a natural, engaging manner as if describing the scene to someone who cannot see it.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error generating caption: {str(e)}"
    
    def generate_alt_text(self, image: Image.Image) -> str:
        prompt = """
        Create concise, descriptive alt-text for this image that would be suitable for web accessibility.
        The alt-text should:
        - Be brief but informative (under 125 characters ideal)
        - Describe the essential visual information
        - Be useful for screen readers
        - Avoid redundant phrases like "image of" or "picture showing"
        - Focus on the most important elements
        
        Return only the alt-text, no additional explanation.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            return response.text.strip()
        except Exception as e:
            return f"Error generating alt-text: {str(e)}"
    
    def generate_keywords_and_tags(self, image: Image.Image) -> List[str]:
        prompt = """
        Analyze this image and generate a list of relevant keywords and tags.
        Include:
        - Objects and subjects in the image
        - Activities or actions
        - Locations or settings
        - Emotions or moods conveyed
        - Colors (if significant)
        - Style or category (e.g., portrait, landscape, abstract)
        
        Return the keywords as a comma-separated list, with each keyword being 1-3 words max.
        Focus on the most relevant and searchable terms.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            keywords = [tag.strip() for tag in response.text.split(',')]
            return keywords[:15] 
        except Exception as e:
            return [f"Error generating tags: {str(e)}"]
    
    def generate_social_media_caption(self, image: Image.Image) -> str:
        prompt = """
        Create an engaging social media caption for this image.
        The caption should:
        - Be engaging and shareable
        - Include relevant hashtags
        - Be appropriate for platforms like Instagram or Twitter
        - Capture the mood or story of the image
        - Be conversational and authentic
        
        Keep it under 280 characters if possible.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error generating social media caption: {str(e)}"

def main():
    st.markdown('<h1 class="main-header">VisionCraft - AI-Powered Multimodal Image Analysis & Caption Generation</h1>', unsafe_allow_html=True)
    
    st.sidebar.header("🔧 Configuration")
    
    api_key = st.sidebar.text_input(
        "Enter your Google Gemini API Key:",
        type="password",
        help="Get your API key from https://makersuite.google.com/app/apikey"
    )
    
    if not api_key:
        st.sidebar.warning(" Please enter your Gemini API key to use the application.")
        st.info("""
        ##  Getting Started
        
        1. **Get your API key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to get your free Gemini API key
        2. **Enter the key** in the sidebar
        3. **Upload an image** and start generating captions!
        
        ### 🌟 Features:
        - **Detailed Descriptions**: Comprehensive image analysis
        - **Alt-Text Generation**: Web accessibility compliant descriptions
        - **Keyword Extraction**: SEO-friendly tags and keywords
        - **Social Media Captions**: Engaging posts ready for sharing
        """)
        return
    
    try:
        captioner = ImageCaptioner(api_key)
        st.sidebar.success("✅ API key configured successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Error configuring API: {str(e)}")
        return
    
    st.markdown("""
    ### 📤 Upload Your Image
    Upload an image and get AI-powered captions, alt-text, and keywords instantly!
    """)
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
        help="Supported formats: PNG, JPG, JPEG, GIF, BMP, WebP"
    )
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption="Uploaded Image", use_container_width=True)
            
            with col2:
                st.markdown("### 📊 Image Details")
                st.write(f"**Format:** {image.format}")
                st.write(f"**Size:** {image.size[0]} × {image.size[1]} pixels")
                st.write(f"**Mode:** {image.mode}")
                if hasattr(uploaded_file, 'size'):
                    st.write(f"**File Size:** {uploaded_file.size:,} bytes")
            
            st.markdown("### 🎯 Generate Content")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📝 Detailed Caption", use_container_width=True):
                    with st.spinner("Generating detailed caption..."):
                        caption = captioner.generate_detailed_caption(image)
                        st.session_state.detailed_caption = caption
            
            with col2:
                if st.button("🔤 Alt-Text", use_container_width=True):
                    with st.spinner("Generating alt-text..."):
                        alt_text = captioner.generate_alt_text(image)
                        st.session_state.alt_text = alt_text
            
            with col3:
                if st.button("🏷️ Keywords & Tags", use_container_width=True):
                    with st.spinner("Generating keywords..."):
                        keywords = captioner.generate_keywords_and_tags(image)
                        st.session_state.keywords = keywords
            
            with col4:
                if st.button("📱 Social Caption", use_container_width=True):
                    with st.spinner("Generating social media caption..."):
                        social_caption = captioner.generate_social_media_caption(image)
                        st.session_state.social_caption = social_caption
            
            st.markdown("### 📋 Results")
            
            if 'detailed_caption' in st.session_state:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### 📝 Detailed Description")
                st.write(st.session_state.detailed_caption)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if 'alt_text' in st.session_state:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### 🔤 Alt-Text (Web Accessibility)")
                st.code(st.session_state.alt_text, language=None)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if 'keywords' in st.session_state:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### 🏷️ Keywords & Tags")
                
                tag_html = '<div class="tag-container">'
                for keyword in st.session_state.keywords:
                    tag_html += f'<span class="tag">{keyword.strip()}</span>'
                tag_html += '</div>'
                st.markdown(tag_html, unsafe_allow_html=True)
                
                st.text_area("Copy Keywords:", ", ".join(st.session_state.keywords), height=100)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if 'social_caption' in st.session_state:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("#### 📱 Social Media Caption")
                st.write(st.session_state.social_caption)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if any(key in st.session_state for key in ['detailed_caption', 'alt_text', 'keywords', 'social_caption']):
                st.markdown("### ⚡ Quick Actions")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🎯 Generate All Content", use_container_width=True):
                        with st.spinner("Generating all content..."):
                            progress_bar = st.progress(0)
                            
                            st.session_state.detailed_caption = captioner.generate_detailed_caption(image)
                            progress_bar.progress(25)
                            
                            st.session_state.alt_text = captioner.generate_alt_text(image)
                            progress_bar.progress(50)
                            
                            st.session_state.keywords = captioner.generate_keywords_and_tags(image)
                            progress_bar.progress(75)
                            
                            st.session_state.social_caption = captioner.generate_social_media_caption(image)
                            progress_bar.progress(100)
                            
                            st.success("✅ All content generated successfully!")
                
                with col2:
                    if st.button("🗑️ Clear All Results", use_container_width=True):
                        for key in ['detailed_caption', 'alt_text', 'keywords', 'social_caption']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.success("🧹 All results cleared!")
                        st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing image: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p> <strong>VisionCraft - AI-Powered Multimodal Image Analysis & Caption Generation</strong></p>
        <p> <strong>Made by Anhad Mahajan</strong></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()