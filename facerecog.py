import face_recognition
import cv2
import numpy as np



def trainface():
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')


    image=face_recognition.load_image_file("image.jpg")
    face_encoding = face_recognition.face_encodings(image)[0]
