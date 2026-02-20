# 🌆 SnapFix — AI Urban Issue Reporter
SnapFix is an AI-powered Telegram bot that enables citizens to report urban civic issues (potholes, garbage, illegal parking, etc.) using photos and location.  
The system classifies issues using Computer Vision + NLP and automatically routes them to the appropriate municipal departments.
. 🎯 Aligned with **UN SDG 11 – Sustainable Cities and Communities**

---

## 🧠 Problem Statement
Traditional civic complaint systems face:
- Manual classification delays  
- No image verification  
- Incorrect department routing  
- Lack of geo-analytics  
- Slow emergency detection 

SnapFix solves this using AI-based image classification, NLP-driven urgency detection, and automated routing.

---

## 🏗 System Architecture
The system follows a 3-layer architecture:
### 1️⃣ Citizen Layer
- Telegram bot interface
- Users submit `/report` + image + description + location
### 2️⃣ AI Processing Layer
- Image classification (MobileNetV2)
- Text urgency detection (TF-IDF + spaCy)
- Confidence scoring system
- Auto-routing logic
### 3️⃣ Admin & Governance Layer
- Flask REST backend
- PostgreSQL database with spatial indexing
- Admin dashboard with maps & status tracking
### 🔁 Data Flow
```
Citizen → Telegram Bot → Flask API → AI Models → PostgreSQL → Admin Dashboard
                           ↓
                Auto-Route to Departments
```
This modular architecture ensures scalability and maintainability.
---
## 🤖 AI Models & Performance
### 🖼 Image Classification
- Model: MobileNetV2 (Transfer Learning)
- Framework: TensorFlow 2.15
- Dataset: 3,000+ civic issue images
- Classes: 9 urban issue categories
- Test Accuracy: **93.36%**

### Detected Categories:
- Potholes
- Garbage
- Illegal Parking
- Graffiti
- Fallen Trees
- Damaged Concrete
- Road Sign Issues
- Electric Pole Damage
- Power Outages

---

### 📝 Text Urgency Detection
- Vectorization: TF-IDF
- NLP: spaCy v3.7
- Classifier: Logistic Regression
- Dataset: 3,000+ complaint texts
- F1 Score: **99.83%**
Detects emergency phrases like:
- "accident"
- "danger"
- "live wire"
- "road blocked"

---

## ⚡ Smart Auto-Routing System
- 85% of complaints auto-processed without manual intervention  
- Low-confidence cases flagged for review  
- Reduces administrative workload  
- Improves response speed  

---

## 🗄 Tech Stack
| Layer | Technology |
|--------|------------|
| Bot | python-telegram-bot v20.7 |
| Image AI | TensorFlow 2.15, MobileNetV2 |
| Text AI | spaCy 3.7, scikit-learn (TF-IDF) |
| Backend | Flask REST APIs |
| Database | PostgreSQL (Spatial Indexing) |
| Frontend | HTML Admin Dashboard |
| Other | Geo-tagging, Heatmaps |

---

## 📊 Project Results
- Image Classification Accuracy: **93.36%**
- Urgency Detection F1 Score: **99.83%**
- Auto-Routing Efficiency: **85% automated complaints**
- Multimodal AI (Image + Text fusion)
- Geo-aware civic analytics

---

## 🚀 Installation & Setup

### 1️⃣ Clone Repository

```
git clone https://github.com/Saharsha123/SnapFix.git
cd SnapFix
```

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 3️⃣ Run Application

```
python app.py
```

---

## 🌍 Impact & Innovation
- Multimodal AI system (Image + Text)
- Real-time civic complaint routing
- Geo-spatial analytics support
- Dashboard-based governance monitoring
- Supports UN Sustainable Development Goal 11
SnapFix enhances transparency, speeds up civic issue resolution, and reduces manual workload for city authorities.

---

## 🔮 Future Scope
- Cloud deployment (AWS / GCP)
- Mobile app integration
- Real-time department notifications
- Predictive maintenance using complaint heatmaps
- Integration with smart city APIs

---

## 👨‍💻 Team
Saharsha  
Yashas M N  
Samartha K B  
Avyay Bhat  

---

## 📜 License
This project is developed for academic and research purposes.
