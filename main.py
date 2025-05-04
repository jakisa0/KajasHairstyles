#git config --global user.name jakisa0
#git config --global user.name jakakosir5@gmail.com
#pip install tinydb flask

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, flash, get_flashed_messages, session
from tinydb import TinyDB, Query
import os

app = Flask(__name__)
app.secret_key = "skrivni_kljuc_123"

db = TinyDB('KajasHairstyles.json')
stranka = db.table('stranka')
Uporabnik = Query()
kontakt = db.table('kontakt')
termini = db.table("termini")

@app.route("/")
def domov():
    return render_template("domov.html")

@app.route("/rezervacija")
def rezervacija():
    if 'uporabnik' not in session:
        return redirect(url_for('prijava'))
    vsiTermini = termini.all()
    koledarTermini = []
        for t in vsiTermini:
            datum = t["datum"]
            for ura in t["ure"]:
                koledarTermini.append({
                    "title": ura,
                    "start": f"{datum}T{ura}"
                })
    return render_template("rezervacija.html", termini=vsiTermini, koledarTermini=koledarTermini)


@app.route("/rezerviraj", methods=["POST"])
def rezerviraj():
    if 'uporabnik' not in session:
        return redirect(url_for('prijava'))

    datum = request.form["datum"]
    ura = request.form["ura"]

    termin = termini.get(Query().datum == datum)
    if termin and ura in termin["ure"]:
        nove_ure = [u for u in termin["ure"] if u != ura]
        if nove_ure:
            termini.update({"ure": nove_ure}, Query().datum == datum)
        else:
            termini.remove(Query().datum == datum)

        flash(f"Uspešno si rezerviral termin {datum} ob {ura}.")
    else:
        flash("Ta termin ni več na voljo.")

    return redirect(url_for("rezervacija"))

@app.route("/onas", methods=["GET", "POST"])
def onas():
    if request.method == "POST":
        ime = request.form["ime"]
        email = request.form["email"]
        sporocilo = request.form["sporocilo"]

        kontakt.insert({
            "ime": ime,
            "email": email,
            "sporocilo": sporocilo
        })

        flash("Hvala za vaše sporočilo!")
        return redirect(url_for('onas'))
    
    return render_template("onas.html")

@app.route("/vsa-sporocila")
def vsa_sporocila():
    if session.get("admin"):
        return jsonify(kontakt.all())
    return "Dostop zavrnjen", 403

@app.route("/dodaj-termin", methods=["POST"])
def dodaj_termin():
    if not session.get("admin"):
        return "Dostop zavrnjen", 403

    datum = request.form["datum"]
    ure_raw = request.form["ure"]
    ure = [u.strip() for u in ure_raw.split(",") if u.strip()]

    #ce je datum ze notr, dodamo ure
    obstojec = termini.get(Query().datum == datum)
    if obstojec:
        nove_ure = list(set(obstojec["ure"] + ure))
        termini.update({"ure": nove_ure}, Query().datum == datum)
    else:
        termini.insert({"datum": datum, "ure": ure})

    return redirect(url_for("rezervacija"))

@app.route('/prijava', methods=['GET', 'POST'])
def prijava():
    if request.method == 'POST':
        uporabnik = request.form['uporabnik']
        geslo = request.form['geslo']
        
        if uporabnik == "admin" and geslo == "123":
            session['uporabnik'] = 'admin'
            session['admin'] = True
            return jsonify({'success': True})

        user = stranka.get(Uporabnik.username == uporabnik)
        if user:
            if user['password'] == geslo:
                session['uporabnik'] = uporabnik
                session['admin'] = False
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Napačno geslo'})
        
        stranka.insert({'username': uporabnik, 'password': geslo})
        session['uporabnik'] = uporabnik
        session['admin'] = False
        return jsonify({'success': True})
    
    return render_template('prijava.html')

@app.route('/odjava')
def odjava():
    session.pop('uporabnik', None)
    return redirect(url_for('domov'))

if __name__ == "__main__":
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)