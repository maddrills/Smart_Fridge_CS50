import os
import ast
import datetime
from datetime import date
import requests
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, g


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = g

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///items.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response




@app.route("/",methods=["GET", "POST"])
@login_required
def index():
    un_updated_weights = 0
    idz = []
    bds = []
    #the below was to grab data from the cloud but due to latency and
    #poor dinamisim i rejected the idea and try an alternative aproch
    #the latency time was $ - 10 min per refresh
    '''
    # here is where i want to display in fridge items
    data = requests.get('https://thingspeak.com/channels/1713402/feed.json').content

    #after importing the ast lib
    #the data sete is is taken in as a bytes formate hense the entire dictionary is encased in a b"{} formate
    #below convertes it to a normal datatype
    dict_str = data.decode("UTF-8")
    my_data = ast.literal_eval(dict_str)

    print(repr(my_data))
    print(my_data["feeds"])
    #print(str(data))
    return render_template("homepage.html",my_data = my_data["feeds"])
    '''

    # now i need to add an option to reset the folowing data fields
    #1)data
    #2)master_weight
    #3)old_weight
    # use DELETE FROM table_name; on all mentiond
    if request.method == "POST":
        #get product code
        add = request.form.get("add")
        if add:
            #print(add)
            #GET PRODUCT table
            try:
                number = db.execute("SELECT pin FROM products WHERE pin = ?",add)[0]["pin"]
            except:
                return apology("unregisterd product")

            if add:
                session["productw"] = number
                return redirect("/")
            #run
        stum = request.form.get("dil")
        dore = request.form.get("dore")
        try:
            code_number = session["productw"]
        except:
            return redirect("/")

        print(stum)
        if stum == "del":
            #delete all mentiond fields for db
            #1)data
            db.execute("DELETE FROM data WHERE code = ?",code_number)
            #2)master_weight
            db.execute("DELETE FROM master_weight WHERE code = ?",code_number)
            #3)old_weight
            db.execute("DELETE FROM old_weight WHERE code = ?",code_number)
            #3)scaned_tag
            db.execute("DELETE FROM scaned_tag WHERE product_code = ?",code_number)
            #4)reset all fields of repository
            db.execute("DELETE FROM repository WHERE product_code = ?",code_number)
            #5)set all bought now weights to 0
            db.execute("UPDATE transactions SET now_amount = 0, last_used_time = ? WHERE user_id = ?","None",session["user_id"])
            return redirect("/")
        #i have to make a close dore function / update function
        print("dore = ",dore)
        if dore == "remove":

            #find weights that arnt = to updated weight or master_weight
            try:
                master_weight = db.execute("SELECT master_weight FROM master_weight WHERE code = ?",code_number)[0]["master_weight"]#read
                un_updated = db.execute("SELECT product_total FROM repository WHERE product_total > ?",master_weight)
                #idz =  db.execute("SELECT scaned_tag FROM scaned_tag")
                #db.execute("UPDATE old_weight SET old_weight = ?",0)

            except:
                un_updated = -3000
                print("error")
            #this will add all the un updated repository(total_weights) to 0 indicating they are outside the fridge
            count = 0
            if un_updated != -3000:
                #will del id not in use
                '''
                for j in idz:
                    #select all idz
                    number = idz[count]["scaned_tag"]
                    # del the rfid not in fridge
                    db.execute("DELETE FROM scaned_tag WHERE scaned_tag = ?",number)
                    '''
                count = 0
                for i in un_updated:
                    un_updated_weights = un_updated[count]["product_total"]
                    if master_weight and master_weight < un_updated_weights:
                        print(un_updated_weights)
                        #change the unpudated total weight field to
                        db.execute("UPDATE repository SET product_weight = ?,product_total = ? WHERE product_total = ? AND product_code = ?",0,0,un_updated_weights,session["productw"])
                        the_id = db.execute("SELECT product_rfid FROM repository WHERE product_total = ?",0)[0]["product_rfid"]
                        db.execute("DELETE FROM scaned_tag WHERE scaned_tag = ?",the_id)
                        count+=1
        #here i need to create the count for all the bought itms

        return redirect("/")
    else:
        #give an option to enter the product number to add to page
        items = db.execute("SELECT * FROM transactions WHERE user_id = ?",session["user_id"])
        #print(items)
        #code = request.form.get("product_code")
        data_of_id = db.execute("SELECT badge_number FROM transactions WHERE badge_number != ?","rfid")
        count = 0
        for j in data_of_id:
            #this we can use to put rf in a list
            idz.append(data_of_id[count]["badge_number"])
            count+=1
        #print(idz)

        #print("the data",idz)
        #HERE compaire the list to the repository data
        try:
            repository = db.execute("SELECT product_rfid FROM repository WHERE product_code == ?",session["productw"])
        except:
            print("something went wrong")
            return render_template("homepage.html")
        count = 0
        for j in repository:
            #this we can use to put rf in a list
            bds.append(repository[count]["product_rfid"])
            count+=1
        #print(bds)

        count = 0
        #idz is the count in transaction the othere(bds) is repository
        for j in idz:
            #print comepair j value
            if j in bds:
                #gwt the date and time from repository
                the_date_time = db.execute("SELECT 	last_used_date_time FROM repository WHERE product_code = ? AND product_rfid = ?",session["productw"],j)[count]["last_used_date_time"]
                #get values as per j from repository
                the_got_value = db.execute("SELECT product_weight FROM repository WHERE product_rfid = ? AND product_code = ?",j,session["productw"])[count]["product_weight"]

                #only then update the field value
                try:
                    db.execute("UPDATE transactions SET now_amount = ? WHERE badge_number = ? AND user_id = ?",the_got_value,j,session["user_id"])
                    db.execute("UPDATE transactions SET last_used_time = ? WHERE badge_number = ? AND user_id = ?",the_date_time,j,session["user_id"])

                    #change all non zero values to status to 1
                    db.execute("UPDATE transactions SET status = ? WHERE now_amount != ? AND user_id = ?","IN",0,session["user_id"])
                    db.execute("UPDATE transactions SET status = ? WHERE now_amount == ? AND user_id = ?","OUT",0,session["user_id"])
                except:
                    print("error")



        return render_template("homepage.html",items = items)






@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username ? udes to plug in
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or  via redirect)
    else:
        return render_template("login.html")







@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")






@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #nead to accept user respone with pasword ver
    if request.method == "POST":
        #here i need to submit the users input
        #the input shoud be added to the database
        # hash the useres input
        if not request.form.get("username"):
            #must r4ender or return apology that user is
            return apology("empty name")
            #check databse and search if username alerdy excists
        if not request.form.get("password"):
            #if the usere enter a no password return error
            return apology("empty pasword field")
        if not request.form.get("confirmation"):
            #check for the confermation password
            return apology("empty conformation")
            #check if both passwords are the same
        if not request.form.get("password") in request.form.get("confirmation"):
            return apology("password and confermation password dont match")
        else:
            #check databse form the name
            #got to hash the password call hsh function
            hash = generate_password_hash(request.form.get("password"))
            #if name is there then kill program report name taken
            try:
                #else write name to databse and hash pasword
                db.execute("INSERT INTO users(username, hash) VALUES (?,?)" ,request.form.get("username") ,hash)
                return redirect("/")
            except:
                return apology("Name taken")

    return render_template("register.html")






@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    #for now a simulated list of items
    if request.method == "POST":
        selected = request.form.get("rfid")
        print(selected)

        pname = request.form.get("pname")
        pcost = request.form.get("pcost")
        pweight = request.form.get("pweight")
        phidden = request.form.get("phidden")

        print(pname,pcost,pweight,phidden)

        #todays date and time
        today = date.today()
        today = today.strftime('%d-%m-%Y')

        # transfer all the bought fields to the transactions table
        db.execute("INSERT INTO transactions (user_id,badge_number,product_name,amount,exp_date,bought_date,bought_how,now_amount,status) VALUES (?,?,?,?,?,?,?,?,?)",session["user_id"],selected,pname,pweight,phidden,today,"online",0,0)

        list_of_rfid = db.execute("SELECT tag_id FROM tag")
        print(list_of_rfid)

        if selected not in list_of_rfid:
            db.execute("UPDATE tag SET status = ? WHERE tag_id = ?",0,selected)
            return redirect("/buy")
        else:
            return apology("nice try")

    else:
        items = db.execute("SELECT product_name,cost,weight,exp_date FROM items")
        available_tags = db.execute("SELECT tag_id FROM tag WHERE status = 1")
        print(available_tags)
        return render_template("buy.html",items = items,available_tags = available_tags)





@app.route("/items_bought", methods= ["GET","POST"])
@login_required
def items_bought():
    if request.method == "POST":
        #DEL the data
        tag_id = request.form.get("dil")
        #tag back to 1
        try:
            db.execute("UPDATE tag SET status = ? WHERE tag_id = ?",1,tag_id)
        except:
            print("tag was removed already")
            return apology("tag was removed already")
        #now dil the row with tag_data from transactions
        db.execute("DELETE FROM transactions WHERE badge_number = ?",tag_id)
        return redirect("/items_bought")
    else:
        items = db.execute("SELECT * FROM transactions WHERE user_id = ?",session["user_id"])
        return render_template("items_bought.html",items = items)





@app.route("/Mod_offline_bought_data", methods= ["GET","POST"])
@login_required
def Mod_offline_bought_data():
    #name the new item added to fridge item in fridge
    return apology("to code")





@app.route("/shop_keeper", methods= ["GET","POST"])
def shop_keeper():
    temp = []
    if request.method == "POST":
        #then mod the databse with entered values
        product_name = request.form.get("product_name")
        cost = request.form.get("cost")
        weight = request.form.get("weight")
        exp_date = request.form.get("exp_date")
        tag_id = request.form.get("tag_id")
        dell = request.form.get("dil")
        mod = request.form.get("mod")
        mod_id = request.form.get("mod_id")

        #product
        produxt_name = request.form.get("produxt_name")
        pin = request.form.get("pin")

        if dell:
            db.execute("DELETE FROM tag WHERE id = ?;",dell)
            return redirect("/shop_keeper")

        #quick santy check
        if(not (product_name and cost and weight and exp_date) and not(tag_id) and not(dell) and not(mod and mod_id) and not(produxt_name and pin)):
            return apology("blanck space somewhere")
        #now add the data to databse
                #check and processing for product table
        if(product_name and cost and weight and exp_date):
            try:
                #else write tage to databse
                db.execute("INSERT INTO items(product_name,cost,weight,exp_date) VALUES(?,?,?,?)",product_name,cost,weight,exp_date)
                return redirect("/shop_keeper")
            except:
                return apology("conflict")
        if tag_id:
            try:
                #else write tage to databse
                db.execute("INSERT INTO tag(tag_id,status) VALUES(?,?)",tag_id,True)
                return redirect("/shop_keeper")
            except:
                return apology("conflict")

        #for product
        if produxt_name and pin:
            print(produxt_name,pin)
            try:
                #inserting data
                db.execute("INSERT INTO products(product_name,pin) VALUES(?,?)",produxt_name,pin)
                return redirect("/shop_keeper")
            except:
                return apology("conflict")

        check_id = db.execute("SELECT tag_id FROM tag WHERE status = ?",0)
        print(check_id)
        for i in check_id:
            #put in value in list
            temp.append(i["tag_id"])
        # to make id status as 1
        print(temp)
        if mod == "1" and mod_id in temp:
            db.execute("UPDATE tag SET status = ? WHERE tag_id = ?",1,mod_id)
            return redirect("/shop_keeper")
            #change
        else:
            return apology("nice try mr olson")

    temp = []

    feadback = db.execute("SELECT * FROM items")
    feadback2 = db.execute("SELECT * FROM tag")
    feadback3 = db.execute("SELECT tag_id FROM tag WHERE status = ?",0)
    feedback4 = db.execute("SELECT * FROM products")

    return render_template("shop_keeper.html",feadback = feadback, feadback2 = feadback2,feadback3 = feadback3,feedback4 = feedback4)

    #shoud enter items field data manualy





@app.route("/repository",methods=["POST"])
def repository():
    temp = []
    waight_per_id = []
    weight = request.args.get("weight")
    rfid = request.args.get("rfid")
    code = request.args.get("code")
    rfold = request.args.get("rfold")
    #send all info to db
    r = requests.get("https://maddrills-code50-54169128-56v69wrqf7xjx-5000.githubpreview.dev/bounce")
    #print(weight,rfid,code,rfold)
    weight = weight.split(".", 1)
    weight = weight[0]
    read = int(weight)
    nothing = "nothing"

    today_with_time = datetime.datetime.now()
    today_with_time = today_with_time.strftime("%d-%m-%Y %H:%M:%S")


    if rfid and rfid != "not":
        try:
            #else write tage to databse
            db.execute("INSERT INTO repository(product_rfid) VALUES(?)",rfid)
        except:
            print("conflict")
        #add total weight -> rfid(weight)
    if rfid and rfid != "not":
        #update table weight regardless
        db.execute("UPDATE repository SET product_total = ?,product_code = ?, last_used_date_time = ? WHERE product_rfid = ?",read,code,today_with_time,rfid)

    '''
    #here i will rater create a few global functions that gets
    #1)db master_weight
    #2)db old_weight
    #3)and a db that holds 3 fields of data (a)curent (b)privious (c)reduce (d)total (e)code
    #4)add weight function if(master_weight > old_weight)
        #privious = curent - old_weight
    #5)add weight function if(old_weight < master_weight)
        #reduce = old_weight - curent
    #6)with algo is sound but if you add a new db that is solly responsible for checking if the id is entered
    '''



    #THIS WILL EXECUTE ONLY WHEN RF IS NOT PRESENT
    if rfid and rfid == "not" and read < 50 and read > 0:
        try:
            #else write default values to database per cod to databse
            db.execute("INSERT INTO data(current,privous,reduce,total,code) VALUES(?,?,?,?,?)",0,0,0,0,code)
        except:
            print("conflict on data")

        #initalising default values for master = read and old = 0
        try:
            db.execute("INSERT INTO master_weight(master_weight,code) VALUES(?,?)",read,code)
        except:
            print("conflict on master_weightr")
        try:
            db.execute("INSERT INTO old_weight(old_weight,code) VALUES(?,?)",0,code)
        except:
            print("conflict on old_weight")
            #initialise the db for scaned_tag
        try:
            db.execute("INSERT INTO scaned_tag(scaned_tag,product_code) VALUES(?,?)",nothing,code)
        except:
            print("conflict on scaned_tag")


    #make a dictionary to store all the data of scaned_tag
    # get all the values in the scaned_tag
    counter = 0
    scaned_tagz = db.execute("SELECT scaned_tag FROM scaned_tag WHERE product_code = ?",code)
    #puts all the values in temp
    for j in scaned_tagz:
        temp.append(scaned_tagz[counter]["scaned_tag"])
        counter+= 1

    #geting the initialised asigned master weight
    try:
        master_weight = db.execute("SELECT master_weight FROM master_weight WHERE code = ?",code)[0]["master_weight"]#read
        old_weight = db.execute("SELECT old_weight FROM old_weight WHERE code = ?",code)[0]["old_weight"]#0
    except:
        print("error")

    if rfid and rfid != "not" and master_weight >= old_weight and rfid != rfold:
        #put LATEST weight inside master weight
        db.execute("UPDATE master_weight SET master_weight = ? WHERE code = ?",read,code)
        master_weight = db.execute("SELECT master_weight FROM master_weight WHERE code = ?",code)[0]["master_weight"]

        #now update the data(current) into master_weight
        db.execute("UPDATE data SET current = ? WHERE code = ?",master_weight,code)

        #GET CURENT WEIGHT from master
        #now put into curent
        curent = db.execute("SELECT current FROM data WHERE code = ?",code)[0]["current"]
        #now run the insert algorithem (privious = curent - old_weight)
        prous = curent - old_weight
        #now put prous into data privous
        #doesnt have to return any thing yet
        #this shows the value of the scaned product
        if prous != 0 and prous > 0 and rfid != temp:
            print("Value of put",prous)
            db.execute("UPDATE data SET privous = ? WHERE code = ?",prous,code)
            privous = db.execute("SELECT privous FROM data WHERE code = ?",code)[0]["privous"]
            #now update the scaned_tag with a tag and code
            db.execute("INSERT INTO scaned_tag(scaned_tag,product_code) VALUES(?,?)",rfid,code)

            #here you can use values in DATA to update REPOSITORY
            '''update REPOSITORY'''
            '''use privos'''
            db.execute("UPDATE repository SET product_weight = ?,last_used_date_time = ? WHERE product_rfid = ?",privous,today_with_time,rfid)
            #now all i have to do is call this rout in the / db


        #update old_weight to master
        db.execute("UPDATE old_weight SET old_weight = ? WHERE code = ?",master_weight,code)
        #end of structural flow

    print("read ",read)
    #when mass is removed
    if rfid and rfid != "not" and read < old_weight and rfid != rfold:
        print("ran")
        #put LATEST weight inside master weight
        db.execute("UPDATE master_weight SET master_weight = ? WHERE code = ?",read,code)
        master_weight = db.execute("SELECT master_weight FROM master_weight WHERE code = ?",code)[0]["master_weight"]

        #now update the data(current) into master_weight
        db.execute("UPDATE data SET current = ? WHERE code = ?",master_weight,code)

        #GET CURENT WEIGHT from master
        #now put into curent
        curent = db.execute("SELECT current FROM data WHERE code = ?",code)[0]["current"]
        #now run the remove algorithem
        #reduce = old_weight - curent
        rece = old_weight - curent

        if rece != 0 and rece > 0:
            print("Value of take",rece)
            db.execute("UPDATE data SET reduce = ? WHERE code = ?",rece,code)
            privous = db.execute("SELECT reduce FROM data WHERE code = ?",code)[0]["reduce"]
            #here you can use values in DATA to update REPOSITORY
            '''update REPOSITORY'''
            '''use privos'''
            #db.execute("UPDATE repository SET product_weight = ? WHERE product_rfid = ?",privous,rfid)
            #now all i have to do is call this db in / rout


        #update old_weight to master
        db.execute("UPDATE old_weight SET old_weight = ? WHERE code = ?",master_weight,code)
        #end of structural flow
        db.execute("")
    temp = []
    return redirect("/repository")
    '''
    #folow 1)
    #db.execute("SELECT FROM data WHERE code = ?",code)[0][""]
    #db.execute("UPDATE table SET column WHERE condition = ?")
    #master_weight = db.execute("SELECT FROM master_weight WHERE code = ?",code)
    #old_weight = db.execute("SELECT FROM old_weight WHERE code = ?",code)
    '''



#code below is used to update the values based on one scan method
#not efective for non stack removel
'''
    number = 0
    list_of_rfid = db.execute("SELECT product_rfid FROM repository")
    for i in list_of_rfid:
        temp.append(list_of_rfid[number]["product_rfid"])
        number+= 1

    #print(temp)

    #used to scan all waights
    waights_and_id = db.execute("SELECT product_rfid FROM repository WHERE product_weight > ?",read + 15)
    #print("these are the idz",waights_and_id)
    #finaly oooh
    number = 0
    for j in waights_and_id:
        waight_per_id.append(waights_and_id[number]["product_rfid"])
        number+= 1
    print("these are the idz",waight_per_id)
    for k in waight_per_id:
        print(k)
        db.execute("UPDATE repository SET product_weight = ? WHERE product_rfid = ?",0,k)
        #render weight as 0


    # check latest url update
    # folowing is used to check if there is a change in waight
    if rfid in temp and rfid != "not":
        #then put the waight in its position
        print(" ------------ ")
        print(weight,rfid,code,rfold)
        #this will reset waight to 0 for all tags
        db.execute("UPDATE repository SET product_weight = ?,product_code = ? WHERE product_rfid = ?",read,code,rfid)
    temp = []
    return redirect("/repository")
'''




@app.route("/check", methods= ["GET","POST"])
def check():
    if request.method == "POST":
        #update page
        return redirect("/check")
    else:
        all_values = db.execute("SELECT * FROM repository")
        print(all_values)
        return render_template("check.html",all_values = all_values)






@app.route("/bounce")
def bounce():
    return apology("to code")
