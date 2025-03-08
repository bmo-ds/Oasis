# Ursina Oasis Project  

## Setup Instructions  

### 1. Install Dependencies  
You'll need **Python 3.8+** and **Ursina**. If you don’t have Python, grab it from [python.org](https://www.python.org/downloads/).  

### 2. Set Up Virtual Environment (PyCharm Recommended)  
- Open the project in **PyCharm** (or any editor).  
- Set up a **virtual environment** (venv) in PyCharm:  
  - Go to **File > Settings > Project: [Your Project] > Python Interpreter**  
  - Click **Add Interpreter > Virtualenv Environment**  
  - Select **Create** and pick your Python version.  

### 3. Install Ursina  
Once the venv is set up, open the **terminal** inside PyCharm and run:  

```bash
pip install ursina
```

## 4. Run the Game  
Just hit **Run** on `main.py`

## Running in Bash
```bash
python -m venv venv
venv\Scripts\activate
pip install ursina
python main.py
```

To exit the venv, type:
``` bash
deactivate
```
Done! 🎮🚀