from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import string, random

app = Flask(__name__)
app.config["SECRET_KEY"] = "akevjlevkajidsjvoequehjvuasxdkjeoszaxjficjqol"
sockio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    code = ""
    while True:
        for i in range(length):
            code += random.choice(string.ascii_uppercase)
    
        if code not in rooms:
            break
    
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        room = code

        if name == "":
            return render_template("home.html", error="'Name' left blank, please enter one.", code=code, name=name)

        try:
            if name in rooms[room]["names"]:
                return render_template("home.html", error=f"'{name}' already exists in room, choose different name.", code=code, name=name)
        except:pass

        if join != False and not code:
            return render_template("home.html", error="'Code' left blank, please enter one.", code=code, name=name)

        if create != False:
            room = generate_unique_code(8)
            rooms[room] = {"members": 0, "messages": [], "names": []}
        elif code not in rooms: 
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@sockio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content,to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@sockio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    rooms[room]["names"].append(name)
    print(f"{name} has joined room {room}")

@sockio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    try:
        if name in rooms[room]["names"]:
            rooms[room]["names"].remove(name)
    except:pass
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left room {room}")

if __name__ == "__main__":
    sockio.run(app, debug=True)
