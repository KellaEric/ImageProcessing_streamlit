import streamlit as st
import cv2
import numpy as np
import pyttsx3
from PIL import Image
import io
import threading
import sqlite3
import os
from io import BytesIO
import speech_recognition as sr

# Initialize the database
def init_db():
    conn = sqlite3.connect("image_processing.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            image_name TEXT,
            processing_option TEXT,
            image BLOB
        )
    ''')
    conn.commit()
    conn.close()

def insert_image_data(image_name, processing_option, image_data):
    conn = sqlite3.connect("image_processing.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO images (image_name, processing_option, image)
        VALUES (?, ?, ?)
    ''', (image_name, processing_option, image_data))
    conn.commit()
    conn.close()

# Text-to-speech function
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Describe the app function
def describe_app():
    description = ("Welcome to the Advanced Computer Vision App. "
                   "This application allows you to upload an image or take a photo and apply various image processing techniques. "
                   "You can convert images to grayscale, detect edges, apply blurring effects, perform thresholding, and adjust brightness. "
                   "Additionally, you can download the processed images for further use. Enjoy exploring image processing!")
    text_to_speech(description)

# Recognize speech function
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        text_to_speech("Listening for your command")
        st.write("Listening...")
        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            st.write(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            st.write("Could not understand the audio.")
            return ""
        except sr.RequestError:
            st.write("Could not request results, please check your connection.")
            return ""

# Process image function
def process_image(image, option, brightness=1.0):
    if option == "Grayscale":
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    elif option == "Edge Detection":
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.Canny(gray, 100, 200)
    elif option == "Blurring":
        return cv2.GaussianBlur(image, (15, 15), 0)
    elif option == "Thresholding":
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, thresholded = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return thresholded
    elif option == "Brightness Adjustment":
        image = np.clip(image * brightness, 0, 255).astype(np.uint8)
        return image
    return image

# Sidebar navigation
def sidebar_navigation():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a page", ["Home", "Image Processing", "Processed Images History"])
    return page

# Change background function
def change_background(color):
    st.markdown(f"""
    <style>
    body {{
        background-color: {color};
    }}
    </style>
    """, unsafe_allow_html=True)

# Add exit function with text-to-speech
def app_exit():
    text_to_speech("Thank you for using the Advanced Computer Vision App. Have a great day!")

# Main function
def main():
    # Sidebar for navigation
    page = sidebar_navigation()

    # Option to change background
    background_color = st.selectbox("Choose a background color:", ["White", "Lightblue", "Lightgreen", "Lightpink"])
    change_background(background_color.lower())

    # Initialize the database
    init_db()

    # Home page
    if page == "Home":
        st.title("Welcome to the Advanced Computer Vision App!")
        st.write("This is an interactive image processing app with a backend to store image data and processed results.")
        
        # Describe the app with text-to-speech
        if st.button("Hear App Description"):
            describe_app()
        
        # Speech Recognition Button
        if st.button("Use Voice Command"):
            command = recognize_speech()
            if "describe" in command:
                describe_app()

    # Image processing page
    elif page == "Image Processing":
        st.title("Advanced Computer Vision App")
        st.write("Upload an image or take a photo to apply image processing.")
        
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        camera_image = st.camera_input("Take a photo")
        
        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.success("Image successfully uploaded!")
            text_to_speech("Image successfully uploaded")
        elif camera_image is not None:
            image = Image.open(camera_image)
            st.success("Photo captured!")
            text_to_speech("Photo captured")
        
        if image is not None:
            image = np.array(image)
            st.image(image, caption="Original Image", use_column_width=True)
            
            option = st.selectbox("Choose an image processing technique:", 
                                  ["Original", "Grayscale", "Edge Detection", "Blurring", "Thresholding", "Brightness Adjustment"])
            
            brightness = 1.0
            if option == "Brightness Adjustment":
                brightness = st.slider("Adjust Brightness", 0.1, 2.0, 1.0)
            
            processed_image = process_image(image, option, brightness)
            
            if option != "Original":
                st.image(processed_image, caption=f"{option} Image", use_column_width=True, channels="GRAY" if len(processed_image.shape) == 2 else "RGB")
                
                # Convert image to byte data for storage
                _, img_bytes = cv2.imencode(".png", processed_image)
                img_byte_data = BytesIO(img_bytes).getvalue()
                
                # Store image data in the database
                insert_image_data("processed_image.png", option, img_byte_data)
                
                # Allow user to download processed image
                st.download_button("Download Processed Image", data=img_byte_data, file_name="processed_image.png", mime="image/png")
        
        # Speech Recognition for commands
        command = recognize_speech()
        if "grayscale" in command:
            text_to_speech("Grayscale is selected")
        elif "edge detection" in command:
            text_to_speech("Edge Detection is selected")
        elif "blurring" in command:
            text_to_speech("Blurring is selected")
        elif "thresholding" in command:
            text_to_speech("Thresholding is selected")
        elif "brightness" in command:
            text_to_speech("Brightness Adjustment is selected")
    
    # Processed Images History page
    elif page == "Processed Images History":
        st.title("Processed Images History")
        conn = sqlite3.connect("image_processing.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM images")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            for row in rows:
                st.subheader(f"Image: {row[1]}")
                st.write(f"Processing Option: {row[2]}")
                image_data = BytesIO(row[3])
                st.image(image_data, caption=f"Processed Image - {row[1]}", use_column_width=True)
        else:
            st.write("No processed images found.")
    
    # Close App section
    if st.button("Close App"):
        app_exit()

if __name__ == "__main__":
    main()
