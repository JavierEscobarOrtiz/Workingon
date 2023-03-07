from flask import Flask
import jsonify
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True, port=8000)

@app.route('/my-first-api', methods = ['GET'])
def hello():

    name = request.args.get('name')

    if name is None:
        text = 'Hello!'

    else:
        text = 'Hello ' + name + '!'

    return text

# http://127.0.0.1:8000/my-first-api
# http://127.0.0.1:8000/my-first-api?name=Ander

@app.route("/get-iris")
def get_iris():

    import pandas as pd
    url ='https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv'
    iris = pd.read_csv(url)

    return jsonify({
        "message": "Iris Dataset",
        "data": iris.to_dict()
        })

@app.route("/plot-iris")
def plot_iris():

    url ='https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv'
    iris = pd.read_csv(url)

    plt.scatter(iris['sepal_length'], iris['sepal_width'])
    plt.savefig('flask/iris.png')

    return send_file('iris.png')