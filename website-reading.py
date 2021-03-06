"""A script that queries a user for their favorite childhood website, 
their birth year and age when they used it, and then generates a personality reading"""

from bs4 import BeautifulSoup
import json
import requests
import re
import time
import operator
import random


all_words = {}

descriptions = {}

current_year = 2019

descriptions_keep_ratio = .25


# stopwords from https://gist.github.com/sebleier/554280
stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

def main():

	#Open set of English words
	with open('words.json') as f:
	    all_words = json.load(f)

	#Open set of descriptive words to be used as "personality words" later
	with open('descriptions.json') as g:
	    descriptions = json.load(g)["descriptions"];

	#Setup the website_url by asking questions
	users_name = input("*\n*\n*\n*\n*\nHey there! This is a program that peers into your formative internet days and from that, tells you a bit about yourself.\nTo start, what's your name?\n\n")
	birth_year = input("*\n*\n*\n*\n*\nHello "+users_name+"! It's nice to meet you. To give us a bit more information to work with, what year were you born? Please format it with four digits, i.e.: '2019', '1991'.\n\n")
	website_url = input("*\n*\n*\n*\n*\nNow, dig deep into your memories and think of a website you loved to go on in the past. Type it here. Some tips: don't include www. or https://. If your favorite site was google, type it like 'google.com'\n\n")
	age_of_use = input("*\n*\n*\n*\n*\nNow, final question. What age were you when you used that site? Type in a single number, i.e. '9' or '16'.\n\n")
	
	website_year = current_year-((current_year-int(birth_year))-int(age_of_use))
	API_URL = "https://archive.org/wayback/available?url="+website_url+"&timestamp="+str(website_year)

	response  = requests.get(API_URL)
	json_response = json.loads(response.text)
	closest_url = json_response["archived_snapshots"]["closest"]["url"]
	website_response  = requests.get(closest_url)

	#Get HTML of the website from the Internet Archive, closest to the time that they used it.
	data = website_response.text
	soup = BeautifulSoup(data, 'html.parser')
	body = soup.find('body')


	website_keywords = {}

	# Create a dictionary of keywords from the HTML, with words as keys and values as number of occurrences in the HTML.
	for string in soup.stripped_strings:
		words_in_string = string.split(" ")
		for word in words_in_string:
			if word not in stopwords:
				#Check that this is actually an English word
				if word in all_words.keys():
					if re.match('[a-zA-Z]+', word):
						if word not in website_keywords:
							website_keywords[word] = 1
						else:
							website_keywords[word] += 1

	#Sort the keywords based on number of occurence.
	sorted_keywords = sorted(website_keywords.items(), key=operator.itemgetter(1), reverse=True)

	#Make a new dict for the keywords, but set up their values as a points in a distribution, to help randomly pick a keyword later.
	keywords_distribution = {}
	total = 0
	for word_occurrence in sorted_keywords:
		ocurrences = word_occurrence[1]
		total += ocurrences
		keywords_distribution[word_occurrence[0]] = total
	
	chosen_keywords = []

	#Narrow down to 3 keywords by selecting keywords at random, with weight given to keywords with high occurrence.
	for i in range(0,3):
		selected = random.randint(0,total)
		for word in keywords_distribution:
			boundary = keywords_distribution[word]
			if boundary >= selected:
				chosen_keywords.append(word)
				break

	#Narrow down the personality words by chosing randomly (because there are too many of them!)
	random_descriptions = []
	for description in descriptions:
		keep = random.uniform(0, 1)
		if (keep < descriptions_keep_ratio):
			random_descriptions.append(description)
	

	print("* Formulating your reading... Please be patient :)")

	closeness = {}
	# Run API calls to conceptnet to pick personality words closest in relatedness to selected keywords
	for keyword in chosen_keywords:
		for description in random_descriptions:
			closeness_url = "http://api.conceptnet.io/relatedness?node1=/c/en/"+keyword+"&node2=/c/en/"+description;
			closeness_response = requests.get(closeness_url)
			time.sleep(.2)
			try:
				closeness_response_json = closeness_response.json()
				if ("value" in closeness_response_json.keys()):
					value = closeness_response_json["value"]
					if keyword in closeness.keys():
						if closeness[keyword]["value"] < value:
							closeness[keyword]["value"] = value
							closeness[keyword]["bestDescription"] = description
					else:
						closeness[keyword] = {"value":value,"bestDescription":description}
					

			except:
				time.sleep(5) 
		print("*")


	result_string = "*~*~*~*~Your Reading~*~*~*~\n*\n*\nGrowing up, you've been somewhat [X] at your core.\nYou've learned some [X] tendencies in more recent times, "+users_name+".\nTry playing around with a [X] point of view.\n*\n*\n*\nTake a look at your childhood site here: "+closest_url
	
	#Replace reading with selected personality words
	for word in closeness.keys():
		best_description = closeness[word]["bestDescription"]
		result_string = result_string.replace("[X]", best_description, 1)

	print(result_string)


main();