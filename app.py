from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)
import csv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.find_all("div", {"class": "cPHDOP col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding='utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            # print(prod_html)
            commentboxes = prod_html.find_all('div', {'class': "RcXBOT"})
            reviews = []
            for commentbox in commentboxes:
                try:
                    name_tag = commentbox.find('p', {'class': '_2NsDsF AwS1CA'})
                    name = name_tag.text.strip() if name_tag else "No Name"

                except Exception as e:
                    logging.info(f"name: {e}")
                    name = "No Name"

                try:
                    rating_tag = commentbox.find('div', {'class': '_3LWZlK'})
                    rating = rating_tag.text.strip() if rating_tag else "No Rating"
                except Exception as e:
                    logging.info(f"rating: {e}")
                    rating = "No Rating"

                try:
                    commentHead_tag = commentbox.find('p', {'class': '_2-N8zT'})
                    commentHead = commentHead_tag.text.strip() if commentHead_tag else "No Comment Heading"
                except Exception as e:
                    logging.info(f"commentHead: {e}")
                    commentHead = "No Comment Heading"

                try:
                    custComment_tag = commentbox.find('div', {'class': ''})
                    custComment = custComment_tag.text.strip() if custComment_tag else "No Comment"
                except Exception as e:
                    logging.info(f"custComment: {e}")
                    custComment = "No Comment"

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead, "Comment": custComment}
                reviews.append(mydict)
            logging.info("log my final result {}".format(reviews))
            filename = f"{searchString}.csv"
            with open(filename, "w", newline='', encoding="utf-8-sig") as fw:
                writer = csv.DictWriter(fw, fieldnames=["Product", "Name", "Rating", "CommentHead", "Comment"])
                writer.writeheader()
                writer.writerows(reviews)
            
            uri = "mongodb+srv://manishd00:pwskills@cluster0.wutq5w0.mongodb.net/?appName=Cluster0"
            # Create a new client and connect to the server
            client = MongoClient(uri, server_api=ServerApi('1'))
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)
            db = client['flipkart_reviews']
            collection = db['reviews_data']
            collection.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.error("Error in review route: %s", e)
            return f"Error: {e}"

    # return render_template('results.html')

    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0")
