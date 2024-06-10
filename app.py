import streamlit as st
import cv2
import os
import shutil
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
gen_api = os.getenv('GEN_AI')

# Function to configure Google Generative AI
def configure_genai(api_key):
    genai.configure(api_key=api_key)

# Function to create or clean up existing extracted image frames directory
def create_frame_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)

# Function to extract frames from video
def extract_frame_from_video(video_file_path, frame_extraction_directory, frame_prefix):
    create_frame_output_dir(frame_extraction_directory)
    vidcap = cv2.VideoCapture(video_file_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    output_file_prefix = os.path.basename(video_file_path).replace('.', '_')
    frame_count = 0
    count = 0
    while vidcap.isOpened():
        success, frame = vidcap.read()
        if not success:  
            break
        if int(count / (fps / 2)) == frame_count: 
            min = (frame_count // 2) // 60
            sec = (frame_count // 2) % 60
            time_string = f"{min:02d}:{sec:02d}"
            image_name = f"{output_file_prefix}{frame_prefix}{time_string}.jpg"
            output_filename = os.path.join(frame_extraction_directory, image_name)
            cv2.imwrite(output_filename, frame)
            frame_count += 1
        count += 1
    vidcap.release()

def video_main():
    st.title("Content Analysis")
    description = """
    <div style="background-color: #48A6EE; padding: 10px; border-radius: 5px; color: black; font-weight: bold;">
        This module allows users to analyzing a social media advertising video and providing insights and suggestions.
    </div>
    """
    st.markdown(description, unsafe_allow_html=True)
    st.write("")

    gen_api = os.getenv('GEN_AI')
    if gen_api:
        configure_genai(gen_api)

    video_file = st.file_uploader("Upload a video file:", type=["mp4", "avi", "mov"])
    if video_file:
        video_path = os.path.join("/tmp", video_file.name)
        with open(video_path, 'wb') as f:
            f.write(video_file.read())
        st.video(video_path)

        frame_extraction_directory = "/tmp/frames"
        frame_prefix = "_frame"
    
        with st.spinner("Processing video..."):
            extract_frame_from_video(video_path, frame_extraction_directory, frame_prefix)

        class File:
            def _init_(self, file_path, response=None):
                self.file_path = file_path
                self.response = response
        
            def set_file_response(self, response):
                self.response = response

        files = os.listdir(frame_extraction_directory)
        files = sorted(files)
        files_to_upload = [File(os.path.join(frame_extraction_directory, file)) for file in files]

        uploaded_files = []
        with st.spinner("Processing video..."):
            for file in files_to_upload:
                response = genai.upload_file(path=file.file_path)
                file.set_file_response(response)
                uploaded_files.append(file)

        prompt = "You are a marketing insights analyst reviewing the uploaded advertising video from my social media page. Describe the key elements and actions in the video. Provide a detailed report in 100-200 words, including insights on the video's effectiveness, audience engagement, and any patterns observed. Offer suggestions for improvement and optimization. Maintain a formal and professional tone."
        if prompt:

            safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]
        
            model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest",safety_settings=safety_settings,)

            def make_request(prompt, files):
                request = [prompt]
                for file in files:
                    request.append(file.response)  # Use response attribute
                return request

            with st.spinner("Processing video..."):
                request = make_request(prompt, uploaded_files)
                response = model.generate_content(request, request_options={"timeout": 600})
                st.markdown(f"""<div style="background-color: #dceefb; padding: 10px; border-radius: 5px; color: black;">{response.text}</div>""", unsafe_allow_html=True)


            with st.spinner("Processing video..."):
                for file in uploaded_files:
                    genai.delete_file(file.response.name)

if __name__ == '__main__':
    video_main()