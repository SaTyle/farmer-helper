from flask import Flask, render_template, request, Markup, redirect
import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError

from utils.disease import disease_dic
from utils.fertilizer import fertilizer_dic
import requests
import config
import pickle
import io
import torch
from torchvision import transforms
from PIL import Image
from utils.model import ResNet9

# email and password to send enquiries to the contact us page
OWN_EMAIL = 'knowndetails2003@gmail.com'
OWN_PASSWORD = 'fsxaajscnzycrryz'



disease_classes = ['Apple___Apple_scab',
                   'Apple___Black_rot',
                   'Apple___Cedar_apple_rust',
                   'Apple___healthy',
                   'Blueberry___healthy',
                   'Cherry_(including_sour)___Powdery_mildew',
                   'Cherry_(including_sour)___healthy',
                   'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
                   'Corn_(maize)___Common_rust_',
                   'Corn_(maize)___Northern_Leaf_Blight',
                   'Corn_(maize)___healthy',
                   'Grape___Black_rot',
                   'Grape___Esca_(Black_Measles)',
                   'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
                   'Grape___healthy',
                   'Orange___Haunglongbing_(Citrus_greening)',
                   'Peach___Bacterial_spot',
                   'Peach___healthy',
                   'Pepper,_bell___Bacterial_spot',
                   'Pepper,_bell___healthy',
                   'Potato___Early_blight',
                   'Potato___Late_blight',
                   'Potato___healthy',
                   'Raspberry___healthy',
                   'Soybean___healthy',
                   'Squash___Powdery_mildew',
                   'Strawberry___Leaf_scorch',
                   'Strawberry___healthy',
                   'Tomato___Bacterial_spot',
                   'Tomato___Early_blight',
                   'Tomato___Late_blight',
                   'Tomato___Leaf_Mold',
                   'Tomato___Septoria_leaf_spot',
                   'Tomato___Spider_mites Two-spotted_spider_mite',
                   'Tomato___Target_Spot',
                   'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
                   'Tomato___Tomato_mosaic_virus',
                   'Tomato___healthy']

disease_model_path = 'models\plant_disease_model.pth'
disease_model = ResNet9(3, len(disease_classes))
disease_model.load_state_dict(torch.load(
    disease_model_path, map_location=torch.device('cpu')))
disease_model.eval()


# newsletter subscription api
def subscribe(email, user_group_email, api_key):
    r = requests.post(
        f"https://api.mailgun.net/v3/lists/{user_group_email}/members",
        auth=('api', api_key),
        data={'subscribed': True,
              'address': email})
    return r


# loading the crop recommendation model
crop_recommendation_model_path = 'models\RandomForest.pkl'
crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))


# ------------------------------------------------------------------------------------------------#
# custom functions
# function to calculate the values of temperature and humidity in crop recommendation

def weather_fetch(city_name):
    """
    Fetch and returns the temperature and humidity of a city
    :params: city_name
    :return: temperature, humidity
    """
    api_key = config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    response = requests.get(complete_url)
    x = response.json()
    if x["cod"] != "404":
        # store the value of "main" key in variable y
        # if __main__ == '__response.json() __':
        y = x["main"]

        temperature = round((y["temp"] - 273.15), 2)
        humidity = y["humidity"]
        return temperature, humidity
    else:
        return None


app = Flask(__name__)
app.debug = True


# home route
@app.route("/", methods=["POST", "GET"])
def home():
    title = 'FARMINGTON'

    def index():
        if request.method == "POST":
            user_email = request.form.get('email')
            response = subscribe(user_email=user_email,
                                 user_group_email='farmington@sandboxc74dffa8f63e4c6f88fc4b3202287d2a.mailgun.org',
                                 api_key='0cfdf4a1d9a6beeab37c3524df66b385-181449aa-a99f71e3')
        return render_template("index.html", title=title)

    return render_template("index.html", title=title)


# route to crop recommendation
@app.route('/crop')
def crop_recommendation():
    title = 'Farmington - Crop Recommendation'
    return render_template('crop.html', title=title)


# route to fertilizer suggestion
@app.route('/fertilizer')
def fertilizer_recommendation():
    title = 'Farmington - Fertilizer Recommendation'
    return render_template('fertilizer.html', title=title)


# route to disease detection
@app.route('/disease')
def disease_detection():
    title = 'Farmington - Disease Detection'
    return render_template('disease.html', title=title)


# Render the result pages of each and every system


# Handle Post Requests -- Crop prediction  Result Page
@app.route('/crop_predict', methods=['POST'])
def crop_prediction():
    title = 'Farmington - Crop Recommendation Result'

    if request.method == 'POST':
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorus'])
        K = int(request.form['potassium'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        # state = request.form.get("stt")
        city = request.form.get("city")

        if weather_fetch(city) != None:
            temperature, humidity = weather_fetch(city)
            data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
            my_prediction = crop_recommendation_model.predict(data)
            final_prediction = my_prediction[0]

            return render_template('crop-result.html', prediction=final_prediction, title=title)

        else:
            title = 'UnExpeted Details 😒'
            return render_template('try_again.html', title=title)


# Handle Post Requests -- Fertilizer Recommendation Result Page
@app.route('/fertilizer_predict', methods=['POST'])
def fert_recommend():
    title = "Farmington - Fertilizer Suggestion"

    # requesting data from the form
    crop_name = str(request.form['cropname'])
    N = int(request.form['nitrogen'])
    P = int(request.form['phosphorus'])
    K = int(request.form['potassium'])
    # ph = float(request.form['ph'])
    df = pd.read_csv('Data\\fertilizer.csv')
    try:
        nr = df[df['Crop'] == crop_name]['N'].iloc[0]
    except IndexError:
        title = "OOPS!Need More Data To Study."
        return render_template('try_again.html', title=title)
    else:
        pr = df[df['Crop'] == crop_name]['P'].iloc[0]
        kr = df[df['Crop'] == crop_name]['K'].iloc[0]

        # finding out the variation in the given input and the model's actual values
        n = nr - N
        p = pr - P
        k = kr - K

        # putting the absolute values of the differences in a dictionary
        temp = {abs(n): 'N', abs(p): 'P', abs(k): 'K'}
        max_value = temp[max(temp.keys())]

        if max_value == 'N':
            if n < 0:
                key = "NHigh"
            else:
                key = "Nlow"

        elif max_value == 'P':
            if p < 0:
                key = "PHigh"
            else:
                key = "Plow"

        else:
            if k < 0:
                key = 'KHigh'
            else:
                key = 'Klow'

        response = Markup(str(fertilizer_dic[key]))
        return render_template('fertilizer-result.html', recommendation=response, title=title)



def predict_image(img, model=disease_model):
    """
    Transforms image to tensor and predicts disease label
    :params: image
    :return: prediction (string)
    """
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.ToTensor(),
    ])
    image = Image.open(io.BytesIO(img))
    img_t = transform(image)
    img_u = torch.unsqueeze(img_t, 0)

    # Get predictions from model
    yb = model(img_u)
    # Pick index with highest probability
    _, preds = torch.max(yb, dim=1)
    prediction = disease_classes[preds[0].item()]
    # Retrieve the class label
    return prediction

@app.route('/disease-predict', methods=['GET', 'POST'])
def disease_prediction():
    title = 'Farmington - Disease Detection'

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return render_template('disease.html', title=title)
    
        # Read the image and convert it to RGB if it has 4 channels
        img = Image.open(file)
        img = img.convert('RGB')
        
        # Convert the image to bytes-like object
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        
        # Get the bytes data from the bytes-like object
        img_bytes = img_bytes.getvalue()
        
        prediction = predict_image(img_bytes)
    
        prediction = Markup(str(disease_dic[prediction]))
        return render_template('disease-result.html', prediction=prediction, title=title)
        
    # return render_template('disease.html', title=title)
    return render_template('disease-result.html',prediction=prediction, title=title)





# Navbar links

@app.route('/aboutus')
def about():
    title = 'Farmington - About Us'
    return render_template('about.html', title=title)


@app.route('/services')
def services():
    title = 'Farmington - Our Services'
    return render_template('services.html', title=title)


@app.route('/faqs')
def faqs_ask():
    title = 'Farmington - FAQ'
    return render_template('faqs.html', title=title)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    title = 'Farmington - CONTACT US '
    if request.method == "POST":
        data = request.form
        send_email(data["fname"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent=True, title=title)
    return render_template("contact.html", msg_sent=False, title=title)


# NEWSLETTER SUBSCRIPTION


def send_email(fname, email, phone, message):
    email_message = f"Subject: New Message \n\nFull Name: {fname}\nEmail:{email}\nPhone:{phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(OWN_EMAIL, OWN_EMAIL, email_message)


if __name__ == '__main__':
    app.run()
