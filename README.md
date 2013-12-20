Spam-Filter-Plus
================

HW6 CIS391 Artificial Intelligence 
Tara Siegel and Joesph Trovato

Base code:
	Started off by integrating our homework 5 naivebayes function into __trainer__ and our classify function into the predict method in the Predictor.py file.  This uses laplace smoothing (m = 1/1000 in our implementation) to calculate the word probabilities.  We added a word to the vocabulary named 'UNKNOWN' that will get the laplace smoothing probability of it never being seen, which should be a tiny number but not 0.  When we predict, if the word has not been seen by the training set it will use the UNKNOWN probability for that particular word. Using naive bayes we simply going through the words in the file we're testing and adding up the log of each of the probability of seeing said word to get a final log probability of it occurring in spam or ham.  We initially are using the nltk tokenizer (word_tokenize() function) to tokenize the training and testing files. 

Things we tried to improve the tokenizer:

First Iteration:
	In the body:
		1. Before using nltk tokenize to break up the words, we stripped out a bunch of things:
			a. transformed everything to lowercase
			b. removed all of the urls
			c. removed all of the content that falls between the <style></style>, <comment></comment>, and <noframes></noframes>
			d. removed all of the &nbsp; , <br> , and <p> tags
			e. removed all of the HTML tags (anything that fit the form of having < >)
			f. removed all of the punctuation
		2. Performed nltk on this stripped text
		3. After being broken up into the initial tokens:
			a. didn't add the word if it was less than 3 letters or more than 13
			b. stripped off the last letter if it was s, so nothing was plural
	By running the modified body tokenizer on the enitre document:
		Ham 196/200
		Spam 186/200

Second Iteration:
	In the header:
		1. Took out the subject line for tokenizing as a seperate classifier
		2. Took out the recipients for tokenizing as a seperate classifier
			a. Got a count of how many recipients there are
		3. Disgarded the rest of the header

	When took out the headers in the initial tokenizing:
		Ham 199/200
		Spam 187/200
