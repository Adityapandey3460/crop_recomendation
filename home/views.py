from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm  # Use the custom form
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import pickle
import numpy as np
import pandas as pd

model = pickle.load(open(r'model-training/model.pkl', 'rb'))
label = pickle.load(open(r'model-training/label.pkl', 'rb'))
columns = pickle.load(open(r'model-training/columns.pkl', 'rb'))



def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Optional: auto-login after signup
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')  # Redirect to home after login
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

import random

# Load your pre-saved crop range dictionary from pickle
with open(r'model-training/crop_ranges_95.pkl', "rb") as f:
    crop_ranges_95 = pickle.load(f)

def generate_crop_reasoning(crop_name, user_input, crop_ranges):
    reasoning = []

    crop_range = crop_ranges.get(crop_name)
    if not crop_range:
        return f"❌ No range data found for '{crop_name}'. Please check crop name or dataset."

    for feature, value in user_input.items():
        if feature not in crop_range:
            continue
        
        low, high = crop_range[feature]
        param = feature.upper()

        if low <= value <= high:
            messages = [
                f"✔ {param} value of {value} is ideal for {crop_name}, within the preferred range ({low}–{high}).",
                f"✅ Your {param} level ({value}) perfectly supports optimal growth of {crop_name}.",
                f"👍 Excellent! {param} is well balanced for {crop_name}, promoting strong yield."
            ]
        elif value < low:
            messages = [
                f"⚠ {param} value of {value} is lower than optimal for {crop_name}. Ideal range is {low}–{high}.",
                f"🔽 {param} is slightly deficient for {crop_name}. Consider increasing it toward {low}.",
                f"⚠ Insufficient {param} might slow down {crop_name} growth. Raise it closer to {low}–{high}."
            ]
        else:  # value > high
            messages = [
                f"⚠ {param} value of {value} is too high for {crop_name}. Recommended range is {low}–{high}.",
                f"🔺 Excess {param} may harm {crop_name}'s growth. Try reducing it below {high}.",
                f"⚡ Too much {param} can stress {crop_name}. Adjust to keep it within {low}–{high}."
            ]

        reasoning.append(random.choice(messages))

    return "\n".join(reasoning)

# Example user input
# user_input = {
#     "N": 90,
#     "P": 42,
#     "K": 43,
#     "temperature": 20.8,
#     "humidity": 82.0,
#     "ph": 6.5,
#     "rainfall": 202.9
# }

# predicted_crop = "apple"

# # Output reasoning
# print(f"\n🌱 Recommendation Reason for '{predicted_crop.upper()}':\n")
# print(generate_crop_reasoning(predicted_crop, user_input, crop_ranges_95))




# def index(request):
#     if request.method == 'POST':
#         nitrogen = request.POST.get('nitrogen')
#         phosphorus = request.POST.get('phosphorus')
#         potassium = request.POST.get('potassium')
#         temperature = request.POST.get('temperature')
#         humidity = request.POST.get('humidity')
#         ph = request.POST.get('ph')
#         rainfall = request.POST.get('rainfall')     
#         user_input = {
#             "N": nitrogen,
#             "P": phosphorus,
#             "K": potassium,
#             "temperature": temperature,
#             "humidity": humidity,
#             "ph": ph,
#             "rainfall": rainfall
#         }
#         print(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall)
#         data = np.array([nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall])
#         df = pd.DataFrame([data], columns=columns)
#         prediction = model.predict(df)
#         global crop
#         crop = label.inverse_transform([prediction])[0]
#         print(crop)
#         global reason
#         reason=generate_crop_reasoning(crop, user_input, crop_ranges_95)
#         print(generate_crop_reasoning(crop, user_input, crop_ranges_95))
#         return redirect('recommend')
#     return render(request, 'new.html')

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        nitrogen = float(request.POST.get('nitrogen'))
        phosphorus = float(request.POST.get('phosphorus'))
        potassium = float(request.POST.get('potassium'))
        temperature = float(request.POST.get('temperature'))
        humidity = float(request.POST.get('humidity'))
        ph = float(request.POST.get('ph'))
        rainfall = float(request.POST.get('rainfall'))

        user_input = {
            "Nitrogen": nitrogen,
            "Phosphorus": phosphorus,
            "Potassium": potassium,
            "temperature": temperature,
            "humidity": humidity,
            "ph": ph,
            "rainfall": rainfall
        }

        print(user_input)

        # Create the DataFrame
        df = pd.DataFrame([list(user_input.values())], columns=list(user_input.keys()))

        # 🔧 Rename the columns to match what the model was trained on
        df.rename(columns={
            'Nitrogen': 'N',
            'Phosphorus': 'P',
            'Potassium': 'K'
        }, inplace=True)

        prediction = model.predict(df)

        global crop
        crop = label.inverse_transform([prediction])[0]

        global reason
        text = generate_crop_reasoning(crop, user_input, crop_ranges_95)
        reason = simplify_text(text)
        print(reason)
        return redirect('recommend')

    return render(request, 'index.html')

    

def recommend_view(request):
    return render(request, "recommend.html", {'crop': crop, 'reason': reason})


import requests

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
headers = {
    "Authorization": "Bearer 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"
}

def simplify_text(text):
    prompt = f"{text}\n\nGive a simplified and informative version of the above text, no need to mention problems—just suggest what to do within 100 words."
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 300
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        result = response.json()
        output = result[0]["generated_text"]
        output = output.replace("Give a simplified and informative version of the above text, no need to mention problems—just suggest what to do within 100 words.", "")
        output =  output.replace(text, "")
        output = output.strip()
        print(output)
        return output
    
    except Exception as e:
        print("Error:", response.status_code, response.text)
        return None
