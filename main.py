
from flask import Flask, jsonify, url_for 
from flask import render_template , request, flash , redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from os import path
from flask_login import LoginManager ,login_user , login_required, logout_user,current_user

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import date

# api 
from flask_restful import Resource, Api , fields , marshal_with
from werkzeug.exceptions import HTTPException 
from flask import make_response
from flask_restful import reqparse
import json


# other function #################################################################

# date string formate convertion  
def date_dmy(dates):
    d = dates[8:]
    m = dates[5:7]
    y = dates[:4]
    return d+"-"+m+"-"+y

def date_ymd(dates):
    d = dates[:2]
    m = dates[3:5]
    y = dates[6:]
    return y+"-"+m+"-"+d

# card status function *********************************
def card_status(id):
    cards = Card.query.get(id)
    if cards.complete == True :
        return "complete"
    else:
        deadline_date =  date_ymd(cards.deadline)
        today = str(date.today())

        if deadline_date < today:
            return "deadline passed"
        else:
            return "pending"



# bild configration of the app #################################################################

app = Flask(__name__)
db = SQLAlchemy()
app.config['SECRET_KEY'] = 'GUNANIDHI3VEDI'
# database connectivity 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"

db.init_app(app)
api = Api(app)




# modles section  #################################################################

class User(db.Model,UserMixin):
    id = db.Column(db.Integer , primary_key = True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    lists = db.relationship("Card_list")

class Card_list(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer , db.ForeignKey("user.id"))
    cards = db.relationship("Card", cascade="all,delete", backref="card")

class Card(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    titles = db.Column(db.String(100))
    content = db.Column(db.String(500))
    deadline = db.Column(db.String(10))
    last_updated = db.Column(db.String(10))
    completion_date = db.Column(db.String(10))
    complete = db.Column(db.Boolean(), nullable=False) 
    card_list_id = db.Column(db.Integer , db.ForeignKey("card_list.id"))




def create_database(app):
    with app.app_context():
        if not path.exists("database.sqlite3"):
            db.create_all()
            print('Created Database!')
    # if not path.exists("database.sqlite3"):
    #     db.create_all(app=app)
    #     print('Created Database!')

create_database(app)




# controlers section  #################################################################

# login related setup code  ********************************
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



# user identification opration ****************************************

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            if password == user.password :
                login_user(user , remember= True)
                flash("logged in successfully." , category = "success")
                return redirect(url_for("home"))
            else :
                flash("Incorrect password , try again.", category="error")
        else:
            flash("username does not exist" , category="error")
        

    return render_template("login.html",user = current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("login")

@app.route("/sign_up" ,methods=["GET","POST"])
def sign_up():
    if request.method == "POST":
        
        username = request.form.get("username")
        name = request.form.get("name")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username exist." , category="error")
        elif password1 != password2:
            flash("Password don\'t match.",category="error")
        else :
            user = User(username = username,password = password1,name = name)
            db.session.add(user)
            db.session.commit()
            login_user(user , remember= True)
            flash("Acount created! " , category="success")
            return redirect(url_for("home"))

    return render_template("sign_up.html",user = current_user)


# home page ***************************************

@app.route("/" ,methods=["GET","POST"])
@login_required
def home():
    return render_template("home.html", user=current_user , card_status = card_status)

# list oprations *******************************************

@app.route('/add_list', methods=["GET" , "POST"])
@login_required
def add_list():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        user_id = current_user.id

        new_list = Card_list(name=name,description=description,user_id=user_id)
        db.session.add(new_list)
        db.session.commit()
        flash("list created! " , category="success")
        return redirect(url_for("home"))
    return render_template("add_list.html", user = current_user)


@app.route('/edit_list/<list_id>',methods=["GET","POST"])
@login_required
def edit_list(list_id):
    card_list = Card_list.query.get(list_id)
    if card_list:
        if request.method == "POST":
            if card_list.user_id == current_user.id:
                name = request.form.get("name")
                description = request.form.get("description")
                card_list.name = name
                card_list.description = description
                db.session.commit()
                flash("list updated! " , category="success")
            return redirect(url_for("home"))
        return render_template("edit_list.html",card_list = card_list,user = current_user)


@app.route('/delete_list/<list_id>')
@login_required
def delete_list(list_id):
    card_list = Card_list.query.get(list_id)
    if card_list:
        if card_list.user_id == current_user.id:
            db.session.delete(card_list)
            db.session.commit()
            flash("list deleted! " , category="success")
    return redirect(url_for("home"))



# card operation ******************************************

@app.route('/<list_id>/add_card' , methods=["GET" , "POST"])
@login_required
def add_card(list_id):
    if request.method == "POST":
        card_list = request.form.get("list")
        titles = request.form.get("title")
        content = request.form.get("content")
        dates = date_dmy(request.form.get("date"))
        complete = request.form.get("complete")  # return none or on 
        if complete == "1":
            complete = True
        else:
            complete = False

        today = date_dmy(str(date.today()))

        new_card = Card(titles=titles, content=content, deadline=dates,last_updated = today , complete=complete, card_list_id=card_list)
        db.session.add(new_card)
        db.session.commit()
        flash("card created! " , category="success")
        return redirect(url_for("home"))

    return render_template("add_card.html", list_id = int(list_id), user = current_user)


@app.route('/edit_card/<list_id>/<card_id>',methods=["GET","POST"])
@login_required
def edit_card(list_id,card_id):
    card = Card.query.get(card_id)
    card_list = Card_list.query.get(list_id)
    if card:
        if request.method == "POST":
            if card_list.user_id == current_user.id and card.card_list_id == card_list.id:
                card_list_selected = request.form.get("list")
                title = request.form.get("title")
                content = request.form.get("content")
                deadline = date_dmy(request.form.get("date"))
                complete = request.form.get("complete")  # return none or on 
                if complete == "1":
                    complete = True
                    completion_date = date_dmy(str(date.today()))
                else:
                    complete = False
                    completion_date = None

                card.card_list_id = card_list_selected    
                card.titles = title
                card.content = content
                card.deadline = deadline
                card.complete = complete
                card.completion_date = completion_date
                card.last_updated = date_dmy(str(date.today()))
                db.session.commit()
                flash("card updated! " , category="success")
            return redirect(url_for("home"))
        return render_template("edit_card.html",card = card,user = current_user , date_ymd = date_ymd)
    # return str(list_id)+"  "+str(card_id)

@app.route('/delete_card/<list_id>/<card_id>')
@login_required
def delete_card(list_id,card_id):

    card_list = Card_list.query.get(list_id)
    card = Card.query.get(card_id)
    if card:
        if card_list.user_id == current_user.id and card.card_list_id == card_list.id:
            db.session.delete(card)
            db.session.commit()
            flash("card deleted! " , category="success")
    return redirect(url_for("home"))


# summary page **************************************************

@app.route('/summary')
@login_required
def summary():

    completed_card_count = 0 
    panding_card_count = 0
    card_count = 0 

    graph_list = []   #contents list with graph 
    list_detail = []
    lists= Card_list.query.filter_by( user_id = current_user.id).all()

    for i in range(0,len(lists)):

        # completed and panding graph
        completed_card = Card.query.filter_by(card_list_id = lists[i].id , complete = 1).all()
        panding_card = Card.query.filter_by(card_list_id = lists[i].id , complete = 0).all()
        total_card = Card.query.filter_by(card_list_id = lists[i].id ).all()
        
        completed_card_count = len(completed_card)
        panding_card_count = len(panding_card)
        card_count = len(total_card)

        list_detail.append([completed_card_count,panding_card_count,card_count])

       
        if( completed_card_count > 0 or panding_card_count > 0 ):
            y=[completed_card_count,panding_card_count]
            labels = ["completed_card_count", "panding_card_count"]
            explode = [0.2, 0]
            plt.pie(y, labels = labels, explode = explode , autopct = lambda p:f'{p:.2f}% ')
            plt.savefig(f"static/image{i}_1.png",transparent=True)
            plt.close('all')
            graph_list.append(i)
            continue
        graph_list.append([i,"no_card"])

    return render_template("summary.html" ,user = current_user , lists=lists , graph_list = graph_list , list_detail = list_detail)






# API section #################################################################

# custom errors ****************************************

class NotFoundError(HTTPException):
    def __init__(self,status_code):
        self.response = make_response("",status_code)

class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message ):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)







# json format ****************************************
# user json format 
output_user_fields = {
    "id" : fields.Integer , 
    "username" : fields.String , 
    "name" : fields.String
}

create_user_prser = reqparse.RequestParser()
create_user_prser.add_argument("username")
create_user_prser.add_argument("name")
create_user_prser.add_argument("password")


# card_list json format 
output_card_list_fields = {
    "id" : fields.Integer , 
    "name" : fields.String,
    "description" :fields.String,
    "user_id" : fields.Integer
}
create_card_list_prser = reqparse.RequestParser()
create_card_list_prser.add_argument("name")
create_card_list_prser.add_argument("description")
create_card_list_prser.add_argument("user_id")

# card json format 
output_card_fields = {
    "id" : fields.Integer , 
    "titles" : fields.String,
    "content" :fields.String,
    "deadline" : fields.String,
    "last_updated" : fields.String,
    "completion_date" : fields.String,
    "complete" : fields.String,
    "card_list_id" : fields.Integer
}

create_card_prser = reqparse.RequestParser()
create_card_prser.add_argument("title")
create_card_prser.add_argument("content")
create_card_prser.add_argument("deadline")
create_card_prser.add_argument("complete")
create_card_prser.add_argument("card_list_id")




# restfull api controler ****************************************



# user *****************

class UserApi(Resource):
    @marshal_with(output_user_fields)
    def get(self,username):
        user = db.session.query(User).filter(User.username == username).first()
        if user:
            return user
        else:
            raise NotFoundError(status_code = 404)
    
    def post(self):
        args = create_user_prser.parse_args()
        username = args.get("username",None)
        name = args.get("name",None)
        password1 = args.get("password",None)

        if username  :
            user = db.session.query(User).filter(User.username == username).first()
            if user :
                raise BusinessValidationError(status_code=409, error_code="BE1001", error_message = "username alrady exist" )
            else :
                user = User(username = username,password = password1,name = name)
                db.session.add(user)
                db.session.commit()
                return "" , 200

                
        else :
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message = "username is required" )


# list ******************

class Card_listAPI(Resource):
    @marshal_with(output_card_list_fields)
    def get(self,user_id,card_list_id):
        card_list = db.session.query(Card_list).filter_by(user_id = user_id, id = card_list_id).first()
        if card_list:
            return card_list
        else :
            raise NotFoundError(status_code = 404)

    @marshal_with(output_card_list_fields)
    def put(self,user_id,card_list_id):
        args = create_card_list_prser.parse_args()
        name = args.get("name",None)
        description = args.get("description",None)
        card_list = db.session.query(Card_list).get(card_list_id)
        user = db.session.query(User).get(user_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )

        elif card_list == None:
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        
        elif card_list.user_id != int(user_id):
            raise BusinessValidationError(status_code=400, error_code="BE1005", error_message = "card_list is not orned by the user" )

        card_list.name = name 
        card_list.description = description
        db.session.commit()
        return card_list
    

    def delete(self,user_id,card_list_id):
        card_list = db.session.query(Card_list).get(card_list_id)
        user = db.session.query(User).get(user_id)
        card_list = db.session.query(Card_list).get(card_list_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )

        elif card_list == None:
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        
        elif card_list.user_id != int(user_id):
            raise BusinessValidationError(status_code=400, error_code="BE1005", error_message = "card_list is not orned by the user " )
        
        db.session.delete(card_list)
        db.session.commit()
        return "" , 200



    def post(self):
        args = create_card_list_prser.parse_args()
        name = args.get("name",None)
        description = args.get("description",None)
        user_id = args.get("user_id",None)


        if user_id :
            user = db.session.query(User).filter(User.id== user_id).first()
            if user ==  None :
                raise BusinessValidationError(status_code=404, error_code="BE1003", error_message = "user not present" )
            elif name == None:
                raise BusinessValidationError(status_code=404, error_code="BE1006", error_message = "card_list name is required" )
            elif user_id == None :
                raise BusinessValidationError(status_code=404, error_code="BE1007", error_message = "user_id is required " )

            else :
                card_list = Card_list(name = name,description= description,user_id = user_id)
                db.session.add(card_list)
                db.session.commit()
                return "" , 200        
        else :
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message = "user_id is required" )



# card *******************
class CardAPI(Resource):

    @marshal_with(output_card_fields)
    def get(self,user_id,card_list_id,card_id):
        user = db.session.query(User).get(user_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )
        card_list = db.session.query(Card_list).get(card_list_id)
        if card_list == None :
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        card = db.session.query(Card).get(card_id)
        if card == None :
            raise BusinessValidationError(status_code=400, error_code="BE1007", error_message = "card not present" )
        card_list = db.session.query(Card_list).get(card_list_id)
        if card_list not in user.lists:
            raise BusinessValidationError(status_code=400, error_code="BE1008", error_message = "card_list is not orned by the user" )
        if card not in card_list.cards:
            raise BusinessValidationError(status_code=400, error_code="BE1009", error_message = "card is not in card_list" )
        return card 

    @marshal_with(output_card_fields)
    def put(self,user_id,card_list_id,card_id):
        args = create_card_prser.parse_args()
        title = args.get("title",None)
        content = args.get("content",None)
        deadline = args.get("deadline",None)
        complete = args.get("complete","False")
        cards_list_id = args.get("card_list_id")

        user = db.session.query(User).get(user_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )
        card_list = db.session.query(Card_list).get(card_list_id)
        if card_list == None :
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        card = db.session.query(Card).get(card_id)
        if card == None :
            raise BusinessValidationError(status_code=400, error_code="BE1010", error_message = "card not present" )
        if card_list not in user.lists :
            raise BusinessValidationError(status_code=400, error_code="BE1008", error_message = "card_list is not orned by the user" )
        if card not in card_list.cards:
            raise BusinessValidationError(status_code=400, error_code="BE1009", error_message = "card is not in card_list" )
        card_list = db.session.query(Card_list).get(cards_list_id)
        if card_list == None :
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        if card_list not in user.lists :
            raise BusinessValidationError(status_code=400, error_code="BE1008", error_message = "card_list is not orned by the user" )

        
        card.titles = title
        card.content = content
        card.deadline = deadline
        if complete == "True":
            card.complete = True
            card.completion_date = date_dmy(str(date.today()))

        else :
            card.complete = False
            card.completion_date = None

        card.last_updated = date_dmy(str(date.today()))
        card.card_list_id = cards_list_id
        db.session.commit()

        return card,200
    

    def delete(self,user_id,card_list_id,card_id):
        user = db.session.query(User).get(user_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )
        card_list = db.session.query(Card_list).get(card_list_id)
        if card_list == None :
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        card = db.session.query(Card).get(card_id)
        if card == None :
            raise BusinessValidationError(status_code=400, error_code="BE1010", error_message = "card not present" )
        card_list = db.session.query(Card_list).get(card_list_id)
        if card_list not in user.lists:
            raise BusinessValidationError(status_code=400, error_code="BE1008", error_message = "card_list is not orned by the user" )
        if card not in card_list.cards:
            raise BusinessValidationError(status_code=400, error_code="BE1009", error_message = "card is not in card_list" )
        
        db.session.delete(card)
        db.session.commit()
        return "" , 200



    def post(self,user_id):
        args = create_card_prser.parse_args()
        title = args.get("title",None)
        content = args.get("content",None)
        deadline = args.get("deadline",None)
        complete = args.get("complete","False")
        cards_list_id = args.get("card_list_id")


        user = db.session.query(User).get(user_id)
        if user == None :
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message = "user not present" )
        card_list = db.session.query(Card_list).get(cards_list_id)
        if card_list == None :
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message = "card_list not present" )
        if card_list not in user.lists :
            raise BusinessValidationError(status_code=400, error_code="BE1008", error_message = "card_list is not orned by the user" )
        card_list = db.session.query(Card_list).get(cards_list_id)

        if complete == "True":
            complete = True
            completion_date = date_dmy(str(date.today()))
        else :
            complete = False
            completion_date = None

        last_updated = date_dmy(str(date.today()))


        card = Card(titles = title , content = content , deadline = deadline , completion_date = completion_date , complete = complete , last_updated = last_updated , card_list_id = cards_list_id  )
        
        db.session.add(card)
        db.session.commit()

        return "",200


        
       

# adding resources ************************************
api.add_resource(UserApi,"/api/user","/api/user/<string:username>")
api.add_resource(Card_listAPI,"/api/card_list","/api/card_list/<user_id>/<card_list_id>")
api.add_resource(CardAPI,"/api/card_list/<user_id>/card","/api/card_list/<user_id>/<card_list_id>/<card_id>")

 


if __name__ == "__main__":
    app.run(debug=True)



