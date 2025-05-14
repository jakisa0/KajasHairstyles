#git config --global user.name jakisa0
#git config --global user.email jakakosir5@gmail.com
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
rezervacije = db.table("rezervacije")

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
        ure = t["ure"]
        
        ureSeznam = []
        if isinstance(ure, str):
            ureRazdeljene = ure.split(",")
            for u in ureRazdeljene:
                u = u.strip()
                if u:
                    ureSeznam.append(u)
        else:
            ureSeznam = ure

        for ura in ureSeznam:
            dogodek = {}
            dogodek["title"] = ura
            dogodek["start"] = datum + "T" + ura
            koledarTermini.append(dogodek)

    return render_template("rezervacija.html", termini=vsiTermini, koledarTermini=koledarTermini)


@app.route("/rezerviraj", methods=["POST"])
def rezerviraj():
    if 'uporabnik' not in session:
        return redirect(url_for('prijava'))

    datum = request.form["datum"]
    ura = request.form["ura"]
    spol = request.form["spol"]
    stil = request.form["stil"]

    cene = {
        "Low Taper Fade": 15,
        "Mid Fade": 17,
        "Buzz Cut": 12,
        "Classic Cut": 14,
        "Balayage": 50,
        "Prameni": 45,
        "Stopničke": 35,
        "Keratinsko ravnanje": 60
    }

    if stil in cene:
        cena = cene[stil]
    else:
        cena = 0

    termin = termini.get(Query().datum == datum)
    if termin and ura in termin["ure"]:
        stare_ure = termin["ure"]
        noveUre = []
        for u in stare_ure:
            if u != ura:
                noveUre.append(u)

        if len(noveUre) > 0:
            termini.update({"ure": noveUre}, Query().datum == datum)
        else:
            termini.remove(Query().datum == datum)

        rezervacije.insert({
            "uporabnik": session.get("uporabnik"),
            "datum": datum,
            "ura": ura,
            "spol": spol,
            "stil": stil,
            "cena": cena
        })

        flash("Uspešno si rezerviral termin {} ob {} za {} ({}) - {} €.".format(datum, ura, spol, stil, cena))
    else:
        flash("Ta termin ni več na voljo.")

    return redirect(url_for("rezervacija"))

@app.route("/odstrani-termin", methods=["POST"])
def odstrani_termin():
    if not session.get("admin"):
        return "Dostop zavrnjen", 403

    datum = request.form["datum"]
    ura = request.form["ura"]

    termin = termini.get(Query().datum == datum)
    if termin and ura in termin["ure"]:
        stareUre = termin["ure"]
        noveUre = []
        for u in stareUre:
            if u != ura:
                noveUre.append(u)

        if len(noveUre) > 0:
            termini.update({"ure": noveUre}, Query().datum == datum)
        else:
            termini.remove(Query().datum == datum)

        flash(f"Termin {datum} ob {ura} je bil odstranjen.")
    else:
        flash("Termin ni bil najden.")

    return redirect(url_for("rezervacija"))

@app.route("/vse-rezervacije")
def vseRezervacije():
    if not session.get("admin"):
        return "Dostop zavrnjen", 403

    vse = rezervacije.all()
    return render_template("vseRezervacije.html", rezervacije=vse)

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
    ureRaw = request.form["ure"]

    ure = []
    razdeljeneUre = ureRaw.split(",")
    for u in razdeljeneUre:
        u = u.strip()
        if u:
            ure.append(u)

    obstojec = termini.get(Query().datum == datum)

    if obstojec:
        zdruzeneUre = obstojec["ure"] + ure
        noveUreSet = set(zdruzeneUre)
        noveUre = list(noveUreSet)
        termini.update({"ure": noveUre}, Query().datum == datum)
    else:
        novTermin = {
            "datum": datum,
            "ure": ure
        }
        termini.insert(novTermin)

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

@app.route("/blog")
def blog():
    objave = [
        {
            "naslov": "Trenutni trendi: frizure za pomlad/poletje 2025",
            "datum": "2025-05-08",
            "vsebina": "V sezoni 2025 so v ospredju naravni videzi, sproščeni valovi in pastelni toni. Za moške so še vedno najbolj priljubljeni low taper fade in buzz cut, medtem ko ženske posegajo po pramenih in balayažu za sončen videz. Če razmišljaš o spremembi, zdaj je pravi čas! Rezerviraj svoj termin in svetovali ti bomo, kateri stil najbolje ustreza tvoji obliki obraza in teksturi las.",
            "slika": "static/slike/trend.jpg"
        },
        {
            "naslov": "Nasveti za nego las po poletju",
            "datum": "2025-04-15",
            "vsebina": "Poletje lahko resno izsuši vaše lase – sonce, morska voda in klor vplivajo na zdravje las. V našem salonu priporočamo globinsko vlaženje in keratinsko nego po poletju, da lasem povrnemo sijaj in mehkobo. Priporočamo tudi redne konice, saj se razcepljeni lasje po poletju še hitreje lomijo. Ne pozabite na termično zaščito, če pogosto uporabljate likalnik ali sušilec!",
            "slika": "static/slike/nega-barve.jpg"
        }
    ]
    return render_template("blog.html", objave=objave)

@app.route("/slike")
def slike():
    potBaza = os.path.join("static", "slike")
    kategorije = ["kratki", "srednji", "dolgi", "moski", "zenske"]
    slikePoKategorijah = {}

    for kategorija in kategorije:
        pot = os.path.join(potBaza, kategorija)
        if os.path.exists(pot):
            slike = []
            datoteke = os.listdir(pot)
            for slika in datoteke:
                ime = slika.lower()
                if ime.endswith(".png") or ime.endswith(".jpg") or ime.endswith(".jpeg") or ime.endswith(".webp"):
                    pot_do_slike = "slike/" + kategorija + "/" + slika
                    slike.append(pot_do_slike)

            kljuc = kategorija.capitalize()
            slikePoKategorijah[kljuc] = slike

    return render_template("slike.html", slikePoKategorijah=slikePoKategorijah)

if __name__ == "__main__":
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)