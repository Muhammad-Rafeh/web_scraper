\# Weston A. Price Article Scraper



This Python script scrapes \*\*all health topic articles\*\* from:



https://www.westonaprice.org/health-topics/



Each article is saved as a \*\*Markdown (.md) file\*\* inside the `articles/` directory and is \*\*automatically grouped by category\*\*.



---



\## 📌 Features



\- Scrapes all health topic articles

\- Converts articles into clean Markdown format

\- Groups articles by category

\- Simple and easy-to-run Python script



---



\## 🧰 Requirements



\- Python \*\*3.9 or higher\*\*

\- Active internet connection



---



\## 📦 Installation \& Usage



```bash

\# 1️⃣ Clone the Repository

git clone https://github.com/YOUR\_USERNAME/web\_scraper.git

cd web\_scraper



\# 2️⃣ Create a Virtual Environment (Recommended)

python -m venv venv



\# Activate the virtual environment

\# Windows:

venv\\Scripts\\activate

\# macOS / Linux:

source venv/bin/activate



\# 3️⃣ Install Dependencies

pip install -r requirements.txt



\# 4️⃣ Run the Scraper

python site1.py



\# 📝 Notes:

\# - The script will automatically create an articles/ folder if it does not exist.

\# - Markdown files are saved using the article title as the filename.

\# - Categories are automatically derived from the website’s structure.