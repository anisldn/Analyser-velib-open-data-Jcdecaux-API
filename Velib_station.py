from pymongo import MongoClient
import pprint 
import threading
import requests, json
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.tools as tls
import numpy as np
import math


client = MongoClient('mongodb://localhost:27017/')
key = ""
ville = "Lyon"	

url = requests.get('https://api.jcdecaux.com/vls/v1/stations?apiKey=' + key + '&contract=' + ville)
db = client.BBDA
collection = db.velib

def collect_data ():
	url = requests.get('https://api.jcdecaux.com/vls/v1/stations?apiKey=' + key + '&contract=' + ville)
	db = client.BBDA
	collection = db.velib
	time = []
	for d in list(url.json()):
		collection.insert(d)
	timer = threading.Timer(7600, collect_data) 
	timer.start() 
	return 0

def convertHeure(heure):
	heureN = datetime.utcfromtimestamp(heure/1000).strftime('%Y-%m-%d %H:%M:%S')
	return heureN

def Velib_stat(station):

	collection = db.velib
	
	velo_dispo = []
	stands_dispo = []
	list_heure = []
	nom_station = []
	position = []
	

	d = collection.aggregate([{"$match":{"name": station}},{"$project":{"_id":0,"available_bike_stands":1,"available_bikes":1,"position":1,"last_update":{"$toDate":"$last_update"}}},{"$sort":{"last_update":1}}])
	#pprint.pprint(list(d))
	for a in list(d):
			for b in a.keys():
				if b in "available_bike_stands":
					stands_dispo.append(a.values()[0])
				if b in "available_bikes":
					velo_dispo.append(a.values()[1])
				if b in "last_update":
					list_heure.append(a.values()[2])
				if b in "nom":
					nom_station.append(a.values()[0])
	pprint.pprint(nom_station)
	labels = ['emprunt','retour']
	sizes = [a['available_bike_stands'],a['available_bikes']]				
	colors = ['lightskyblue', 'lightcoral']
	plt.pie(sizes, labels=labels, colors=colors,autopct='%1.1f%%', shadow=True, startangle=130)
	plt.axis('equal')
	plt.title('Emprunt & Retour : '+str(station))
	plt.savefig('PieChart01.png')
	plt.show()


	
def position_gps_station(): 

	collection = db.velib
	lat = []
	lng = []
	p = collection.distinct("position")
	for a in list(p):
		lat.append(a.values()[0])
		lng.append(a.values()[1])
	#pprint.pprint(lat)
	#pprint.pprint(lng)

	plt.scatter(lng,lat,s=50,color='black')
	plt.title('Position GPS de toutes les stations')
	plt.xlabel('lng')
	plt.ylabel('lat')
	plt.show()


def histo_velo_dispo(heure,taille) : 

	p = collection.aggregate([{"$project":{"_id":0,"name":1,"available_bike_stands":1,"available_bikes":1,"date":{"$toDate":"$last_update"}}},{"$addFields":{"heure":{"$hour":"$date"}}},{"$match":{"heure":heure}}])
	# pprint.pprint(list(p))
	velos_dispo = []
	nom_station = []
	stands_dispo = []
	for a in list(p) :
		velos_dispo.append(a["available_bikes"])
		nom_station.append(a["name"])
		stands_dispo.append(a["available_bike_stands"])
	#pprint.pprint(velos_dispo)

	x = np.arange(len(nom_station[:taille]))
	fig, ax = plt.subplots()
	plt.bar(x, velos_dispo[:taille])
	plt.xticks(x,tuple(nom_station[:taille]))
	plt.xticks(rotation = 'vertical',fontsize = 10)
	plt.title('Disponibilite des velos par station')
	plt.ylabel('velo_dispo',fontsize = 15)
	plt.show()

	x = np.arange(len(nom_station[:taille]))
	fig, ax = plt.subplots()
	plt.bar(x, stands_dispo[:taille])
	plt.xticks(x,tuple(nom_station[:taille]))
	plt.xticks(rotation = 'vertical',fontsize = 9)
	plt.title('Disponibilite des stands par station')
	plt.ylabel('stands_dispo',fontsize = 17)
	plt.show()

	
def distance(a,b):
	R = 6371
	x = (b[1] - a[1]) * math.cos( 0.5*(b[0]+a[0]) )
	y = b[0] - a[0]
	d = R * math.sqrt( x*x + y*y )
	print(int(d))
	return int(d)
	

def prediction_velo(choix,heure,position): #si choix emprunt = 1, 0 pour retour
	if choix == 1:

		j = collection.aggregate([{"$project":{"_id":0,"name":1,"available_bikes":1,"position":1,"date":{"$toDate":"$last_update"}}},{"$addFields":{"heure":{"$hour":"$date"}}},{"$match":{"heure":heure}},{"$sort":{"available_bikes":-1}}])
		# lj = list(j)
		station = list(j)[:30]
		print("Voici les stations ou vous avez le plus de chances de trouver un velo :")
		resultat = []
		proche = 99999999
		for a in station :
			dist = distance(position,(a["position"]["lat"],a["position"]["lng"]))

			resultat.append(({"NOM":a["name"],"Nbr Velo":a["available_bikes"],"Distance":dist}))
			print("NOM",a["name"],"Nbr Velo",a["available_bikes"],"Distance",dist)
			#print("Distance",dist)
			proche = min(proche,dist)
		print(proche)
		pprint.pprint(resultat)
		for i in range(0,len(resultat)):
			if (resultat[i]["Distance"] == proche): 
				#pprint.pprint(resultat[i])
				r = resultat[i]["NOM"]
		
				print("la station la plus proche est : ",r )
	else : 
		j = collection.aggregate([{"$project":{"_id":0,"name":1,"available_bike_stands":1,"position":1,"date":{"$toDate":"$last_update"}}},{"$addFields":{"heure":{"$hour":"$date"}}},{"$match":{"heure":heure}},{"$sort":{"available_bike_stands":-1}}])
		station = list(j)[:30]
		print("Voici les stations ou vous avez le plus de chances de trouver Une place : ")
		resultat = []
		proche = 99999999
		for a in station :
			dist = distance(position,(a["position"]["lat"],a["position"]["lng"]))

			resultat.append(({"NOM":a["name"],"Nbr place":a["available_bike_stands"],"Distance":dist}))
			print("NOM",a["name"],"Nbr place",a["available_bike_stands"])
			print("Distance",dist)
			proche = min(proche,dist)
		print(proche)
		pprint.pprint(resultat)
		for i in range(0,len(resultat)):
			if (resultat[i]["Distance"] == proche): 
				# pprint.pprint(resultat[i])
				z = resultat[i]["NOM"]
		# proche = 
				print("la station la plus proche est : ",z )

	
	


if __name__ == "__main__":
	
	#collect_data()
	#Velib_stat("7030 - QUARTIER GENERAL FRERE")
	#position_gps_station()
	#histo_velo_dispo(21,40)
	prediction_velo(1,20,(45.764726, 4.847453))
