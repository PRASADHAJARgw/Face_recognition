from flask import Flask, jsonify, request, flash, redirect, url_for
import json
import bson
from datetime import datetime
from flask import send_file
import pymongo
import re
from flask_cors import CORS
import random
from werkzeug.utils import secure_filename
import os
import face_recognition
import cv2
import numpy as np
import requests
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from flask_ngrok import run_with_ngrok

# from werkzeug.utils import secure_filename

import mysql.connector

config = {
    'user': 'root',
    'password': 'abhinavmadke@20',
    'host': 'localhost',
    'port': '3306',
    'database': 'facescan',
    'raise_on_warnings': True,
}
mydb = mysql.connector.connect(
    # host="103.14.99.164",
    # port="3306",
    # user="aebas",
    # password="jaishankar@123",
    # database="facescan",
    # raise_on_warnings=True,
    **config
)

# mycursor = mydb.cursor(buffered=True)

app = Flask(__name__)
CORS(app)


@app.route('/addPhoto', methods=['POST'])
def addphoto():

    imagefile = request.files.get('photo')
    if not imagefile:
        return json.dumps("No photo provided"), 400
    data = request.form.get('aadhar')
    aadhar = str(data)
    print(aadhar)
    if not fetch_user_details(aadhar):
        return json.dumps("User not found, check Aadhar"), 400
    mycursor = mydb.cursor()
    ans = {}
    sql = "SELECT * FROM facescan.faces WHERE aadhar ='" + aadhar + "'"
    mycursor.execute(sql)

    myresult = mycursor.fetchall()
    if (len(myresult)):
        # User already present
        return json.dumps(False)
    filename = secure_filename(imagefile.filename)
    imagefile.save(filename)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
    image = face_recognition.load_image_file(filename)
    encoding = face_recognition.face_encodings(image)[0]

    # mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT json_extract(encodings, '$.encoding'),name FROM facescan.faces")

    myresult = mycursor.fetchall()
    if (len(myresult) > 0):
        known_face_encodings = []
        known_face_names = []
        for row in myresult:
            known_face_names.append(row[1])
            test = row[0]
            test = test[1:]
            test = test[:-1]
            test = test.split(",")
            for i in range(0, len(test)):
                test[i] = np.float64(test[i])
            test = np.array(test)
            known_face_encodings.append(test)
        print(known_face_encodings)
        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True

        while True:
            imgPath = filename
            img = cv2.imread(imgPath)
            faces = face_cascade.detectMultiScale(img, 1.3, 5)
            facex = 0
            facey = 0
            facew = 0
            faceh = 0
            print("Faces :", faces)
            rgb_small_frame = img
            name = "Unknown"
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                roi_gray = img[y:y + h, x:x + w]
                roi_color = img[y:y + h, x:x + w]
                facex = x
                facey = y
                facew = w
                faceh = h
                eyes = eye_cascade.detectMultiScale(roi_gray)
                rgb_small_frame = img[facey:facey + faceh, facex:facex + facew]
            if process_this_frame:
                face_locations = face_recognition.face_locations(
                    rgb_small_frame)
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations)
                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(
                        known_face_encodings, face_encoding)
                    name = "Unknown"
                    face_distances = face_recognition.face_distance(
                        known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                    face_names.append(name)

            process_this_frame = not process_this_frame
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                font = cv2.FONT_HERSHEY_DUPLEX
                print("Name :", name)
            break
        cv2.destroyAllWindows()
        if (name == "Unknown"):
            userdetails = fetch_user_details(aadhar)
            name = str(userdetails['name'])
            test = []
            for i in range(0, len(encoding)):
                test.append(encoding[i])
            data = {'encoding': test}
            # mycursor = mydb.cursor()

            sql = "INSERT INTO facescan.faces (aadhar, name, encodings) VALUES (%s, %s, %s)"
            mycursor.execute(sql, (aadhar, name, json.dumps(data),))
            mydb.commit()
            mycursor.close()
            return json.dumps(True)
        else:
            mycursor.close()
            return json.dumps(False)

    else:
        userdetails = fetch_user_details(aadhar)
        name = str(userdetails['name'])
        test = []
        for i in range(0, len(encoding)):
            test.append(encoding[i])
        data = {'encoding': test}
        sql = "INSERT INTO facescan.faces (aadhar, name, encodings) VALUES (%s, %s, %s)"
        mycursor.execute(sql, (aadhar, name, json.dumps(data),))
        mydb.commit()
        mycursor.close()
        return json.dumps(True)


@app.route('/recogFace', methods=['POST', 'GET'])
def recogFace():
    imagefile = request.files.get('photo')
    if not imagefile:
        return json.dumps("No photo provided"), 400
    imagefile.save(imagefile.filename)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
    mycursor = mydb.cursor()

    mycursor.execute(
        "SELECT json_extract(encodings, '$.encoding'),name FROM facescan.faces")

    myresult = mycursor.fetchall()
    known_face_encodings = []
    known_face_names = []
    for row in myresult:
        known_face_names.append(row[1])
        test = row[0]
        test = test[1:]
        test = test[:-1]
        test = test.split(",")
        for i in range(0, len(test)):
            test[i] = np.float64(test[i])
        test = np.array(test)
        known_face_encodings.append(test)
    print(known_face_encodings)
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        imgPath = imagefile.filename
        img = cv2.imread(imgPath)
        faces = face_cascade.detectMultiScale(img, 1.3, 5)
        facex = 0
        facey = 0
        facew = 0
        faceh = 0
        print("Faces :", faces)
        rgb_small_frame = img
        name = "Unknown"
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            roi_gray = img[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            facex = x
            facey = y
            facew = w
            faceh = h
            eyes = eye_cascade.detectMultiScale(roi_gray)
            rgb_small_frame = img[facey:facey + faceh, facex:facex + facew]
        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"
                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)

        process_this_frame = not process_this_frame
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            font = cv2.FONT_HERSHEY_DUPLEX
            print("Name :", name)
        break
    cv2.destroyAllWindows()
    if name == "Unknown":
        return json.dumps(name)
    # mycursor = mydb.cursor()
    ans = {}
    sql = "SELECT * FROM facescan.attendance WHERE name ='" + name + "'"

    mycursor.execute(sql)

    myresult = mycursor.fetchall()
    if len(myresult) == 0:
        # mycursor = mydb.cursor()

        sql = "INSERT INTO facescan.attendance (name, checkin, checkout) VALUES (%s, %s, %s);"
        now = datetime.now()  # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        mycursor.execute(sql, (name, date_time, date_time))
        mydb.commit()
    else:
        # mycursor = mydb.cursor()

        sql = "UPDATE facescan.attendance SET checkin = %s,checkout=%s where name=%s ;"
        now = datetime.now()  # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        mycursor.execute(sql, (date_time, date_time, name))
        mydb.commit()
    mycursor.close()
    return json.dumps(name)


@app.route('/checkDeviceCoordinates', methods=['POST', 'GET'])
def checkDeviceCoordinates():
    data = request.data
    if not data.decode('utf8'):
        return json.dumps("No Data Provided"), 400
    data = json.loads(data.decode('utf8'))
    # device_id=str(data['device_id'])
    device_id = '4ff73dcb-c44f-4f24-a1d3-892cea5b73ee'
    currentlat = str(data['currentlat'])
    currentlon = str(data['currentlon'])
    mycursor = mydb.cursor()
    ans = {}
    sql = "SELECT latitude,longitude FROM facescan.device WHERE device_id ='" + device_id + "'"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    lat = myresult[0][0]
    lon = myresult[0][1]
    lat1 = float(currentlat)
    lon1 = float(currentlon)
    lat2 = float(lat)
    lon2 = float(lon)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    ans = c * r
    mycursor.close()
    return json.dumps(ans)


@app.route('/adminLogin', methods=['POST', 'GET'])
def adminLogin():
    data = request.data
    print(request)
    if not data.decode('utf8'):
        return json.dumps("No Data Provided"), 400
    data = json.loads(data.decode('utf8'))
    username = str(data['username'])
    password = str(data['password'])
    mycursor = mydb.cursor()
    ans = {}
    sql = "SELECT password FROM facescan.admin WHERE username ='" + username + "'"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    x = myresult[0][0]
    mycursor.close()
    if (x == password):
        return json.dumps(True)
    return json.dumps(False)


def fetch_user_details(aadhar):
    mycursor = mydb.cursor()
    ans = {}
    sql = "SELECT * FROM facescan.users WHERE aadhar ='" + aadhar + "'"

    mycursor.execute(sql)

    myresult = mycursor.fetchall()

    for x in myresult:
        ans['aadhar'] = x[0]
        ans['name'] = x[1]
        dt = str(x[2])
        date = dt[8:] + "-" + dt[5:7] + "-" + dt[:4]

        ans['dob'] = date
        ans['gender'] = x[3]
        ans['city'] = x[4]
        ans['state'] = x[5]
        ans['district'] = x[6]
        ans['pincode'] = x[7]
    mycursor.close()
    return ans


@app.route('/getUserDetails', methods=['POST', 'GET'])
def getUserDetails():
    data = request.data
    if not data.decode('utf8'):
        return json.dumps("No Data Provided"), 400
    data = json.loads(data.decode('utf8'))
    aadhar = str(data['aadhar'])
    ans = fetch_user_details(aadhar)
    if ans:
        return json.dumps(ans)
    return json.dumps(False)


@app.route('/', methods=['POST', 'GET'])
def getpage():
    return json.dumps("FACE SCAN API")


@app.route('/getusers', methods=['POST', 'GET'])
def getusers():
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM facescan.users")
    myresult = mycursor.fetchall()
    users = []
    for x in myresult:
        ans = {}

        ans['aadhar'] = x[0]
        ans['name'] = x[1]
        dt = str(x[2])
        date = dt[8:] + "-" + dt[5:7] + "-" + dt[:4]
        ans['dob'] = date
        ans['gender'] = x[3]
        ans['city'] = x[4]
        ans['state'] = x[5]
        ans['district'] = x[6]
        ans['pincode'] = x[7]
        users.append(ans)
    mycursor.close()
    return json.dumps(users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
