import csv
import json
import requests
from flask import Flask, jsonify
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB

complete_data = []
labels = []

with open("steam_data.csv", 'r') as f:
    csvreader = csv.reader(f)
    csvreader.next() # to read out headers
    for x in csvreader:
        data = []
        labels.append(x[10] in ["Banned", "Probation"] or x[11] in ["Banned", "Probation"])
        for i in [
            4, # cvstate
            5, # profilestate
            # 8, # country code
            # 9, # privacy
            # 11, # vacbanned
            12, # scammerfriends
            13, # repbanscount
            14, # game_count
            # 15, # totaltime
            # 16, # 2weektime
             ]:
            if x[i] == "N/A" or x[i] == "---" or x[i].strip() == "":
                data.append(0)
            else:
                data.append(int(x[i]))
        complete_data.append(data)


NUMBER = 76000

clf = GaussianNB()
clf.fit(complete_data[:NUMBER], labels[:NUMBER]) # 0 to 75999
rf = RandomForestClassifier(n_estimators=100)
rf.fit(complete_data[:NUMBER], labels[:NUMBER]) # 0 to 75999

print "Trained"

app = Flask(__name__)

@app.route("/<steam_id>")
def classify(steam_id=None):
    print "Got request for", steam_id
    if steam_id is None:
        return jsonify(success=False, message="Please call the url in the form /<steam_id>")

    initial = steam_id
    try:
        _ = int(steam_id)
    except:
        print "Converting", steam_id, "into steam id base 64"
        data = requests.get("http://steamid.co/php/api.php?action=steamID&id=" + steam_id)
        steam_id = data.json().get("steamID64", "fail")
        try:
            _ = int(steam_id)
        except:
            print "Could not get base64 steamid"
            return jsonify(success=False, message="Could not get ID")
        print "Found base64 steamID", steam_id

    # service written by [rush-skills] in order to crawl information needed for classifying.
    info = requests.get("http://steam-info.herokuapp.com/info/" + steam_id).json()
    print "Parsing data", info
    classify_info = [info['cvstate'], info['profilestate'],
                     info['scammerfriends'], info['repbanscount'], info['game_count']]
    result_naive = clf.predict(classify_info)
    result_rf = rf.predict(classify_info)
    print "Classified as", result_naive, result_rf

    with open("steam_log.log", "a+") as f:
        f.write(", ".join([str(initial), str(steam_id), str(result_naive[0]), str(result_rf[0]), "\n"]))

    return jsonify(success=True, result1=bool(result_naive[0]), result2=bool(result_rf[0]))

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', threaded=True)
