# List-and-card-management-


# Local_setup ################################################

# Creating virtual environment  
- `python -m venv .env`
# Activate the virtual environment 
- `.env\Scripts\activate`

# Install all the required packages
- `pip inatall -r requirements.txt`

# Start the server
- `python main.py`


## Folder Structure ################################################

- `static` - default `static` files folder. It serves at '/static' path.
- `static/style.css` Custom CSS.
- `templates` - Default flask templates folder
- `api.ymal` - API code
- `database.sqlite3` - sqlite database file 
- `documentation` - project documentation file
- `main.py` - main code file

```

├── database.sqlite3
├── main.py
├── api.ymal
├── documentation.pdf
├── readme.md
├── requirements.txt
├── static
│   └── style.css
└── templates
    ├── add_card.html
    ├── add_list.html
    ├── base2.html
    ├── edit_card.html
    ├── edit_list.html
    ├── home.html
    ├── login.html
    ├── sign_up.html
    └── summary.html
```
