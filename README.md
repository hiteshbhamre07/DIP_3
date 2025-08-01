# 🚀 Data_CRM-DIP3

CRM-DIP3 is a Django-based web application built for managing campaign deliveries, lead tracking, and reporting via dashboards and CSV integrations.

---

## 📂 Project Structure
Data_CRM-DIP3/
├── apps/
│   ├── authentication/
│   ├── dashboard/
│   ├── home/
│   ├── reports/
│   ├── static/
│   ├── suppression/
│   ├── templates/
│   ├── templatetags/
│   └── transform/
├── core/
├── media/
├── staticfiles/
├── venv/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md






---

## 💡 Features

- ✅ Campaign lead delivery & suppression checks
- 📈 Interactive dashboards (Chart.js)
- ⬆️ CSV lead uploads
- 🔍 Rejected lead analysis (Client feedback insights)
- 📄 One-click PDF report generation
- 🧩 Modular Django apps under `/apps/`

---

## ⚙️ Setup Instructions

```bash
# Clone the repo
git clone git@github.com:hiteshbhamre07/DIP_3.git
cd DIP_3

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # For Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver.



---

### ✅ Final Step

After adding both files:

```bash
git add .gitignore README.md
git commit -m "Added .gitignore and README.md for Rover-DIP3 project"
git push
