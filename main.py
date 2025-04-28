#git config --global user.name jakisa0
#git config --global user.name jakakosir5@gmail.com
#pip install tinydb flask

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from tinydb import TinyDB, Query
import os

app = Flask(__name__)
app.secret_key = "skrivni_kljuc_123"

db = TinyDB('KajasHairstyles.json')
stranka = db.table('stranka')
Uporabnik = Query()


@app.route("/")
def domov():
    return render_template("domov.html")

@app.route("/rezervacija")
def rezervacija():
    return render_template("rezervacija.html")

@app.route('/prijava', methods=['GET', 'POST'])
def prijava():
    if request.method == 'POST':
        uporabnik = request.form['uporabnik']
        geslo = request.form['geslo']
        stranka = users.get(User.uporabnik == uporabnik)
        
        if stranka:
            if stranka['geslo'] == geslo:
                session['uporabnik'] = uporabnik
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Napačno geslo'})
        
        users.insert({'uporabnik': uporabnik, 'geslo': geslo})
        session['uporabnik'] = uporabnik
        return jsonify({'success': True})
    
    return render_template('prijava.html')

if __name__ == "__main__":
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)