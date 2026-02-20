# SnapFix--AI-Urban-Issue-Reporter
SnapFix is a Telegram bot that lets people report city problems like potholes or garbage etc easily with photos and location. It uses AI to classify issues and send them to the right city teams fast. This helps make cities cleaner and safer, linked to SDG 11.

## Key Features
* __Easy Reporting:__ Type /report, add photo/description/location in Telegram chat.
* __AI Image Analysis:__ MobileNetV2 model (93.36% accuracy) spots 9 issue types: potholes, garbage, illegal parking, graffiti, fallen trees, damaged concrete, road signs, electric poles, power outages.
* __Text Urgency Check:__ TF-IDF + spaCy NLP (99.83% F1-score) flags emergencies like "danger" or "accident".
​* __Smart Routing:__ High-confidence complaints auto-sent to teams; others flagged for review.
* __Admin Dashboard:__ Web view with maps, status tracking, role-based login.
* __Data Storage:__ PostgreSQL with location support for analytics.

## System Architecture
The app follows a 3-layer design:
1. __Citizen Layer:__ Telegram bot receives complaints.
2. __AI Layer:__ Processes images/text, scores confidence.
3. __Admin Layer:__ Flask backend + database + dashboard.
```
Citizen → Telegram Bot → Flask API → AI Models → PostgreSQL → Dashboard
                ↓
    Auto-Route to Departments
```

## Tech Stack
| Component | Tools                             |
| --------- | --------------------------------- |
| Bot       | python-telegram-bot v20.7         |
| AI Images | TensorFlow 2.15, MobileNetV2      |
| AI Text   | spaCy v3.7, scikit-learn (TF-IDF) |
| Backend   | Flask REST APIs                   |
| Database  | PostgreSQL (spatial indexes)      |
| Frontend  | HTML dashboard                    |
| Other     | Geo-tagging, heatmaps             |
* All trained on 3,000+ civic images and 3,000+ complaint texts.

## Project Results
* __Image Accuracy:__ 93.36% on test set.
* __Urgency Detection:__ 99.83% F1-score.
* __Auto-Routing:__ 85% complaints processed without human check.
* Beats traditional systems by adding location/photos, reducing manual work.

## Team & Credits
* Students: Saharsha | Yashas M N | Samartha K B | Avyay Bhat
* SDG 11 Alignment: Safe, sustainable urban communities.
