# Steps to replicate

* create a virtual environment and install all the packages
```python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
* run the application
```bash
gunicorn run:app --bind 0.0.0.0:5000 --reload 
```