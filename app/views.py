from __future__ import print_function
from flask import request, redirect, url_for, render_template, jsonify
from app import app
from werkzeug import secure_filename
import os
import sys
import pickle


UPLOAD_FOLDER = 'app/files/'
ALLOWED_EXTENSIONS = set(['csv'])
ALLOWED_GRAPHTYPES = set(['line', 'pie', 'donut', 'spline', 'area'])


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return render_template('graph.html', filename=filename) 

	return render_template('upload_file.html') 

@app.route('/dumpgraphdata')
def dumpgraphdata():
	filename = request.args.get('filename')
	fp = open(UPLOAD_FOLDER+"/"+filename)
	delimiter = ","
	header = fp.readline()
	header = header.strip()

	result = {}
	colmapper = {}
	count = 0

	for col in header.split(delimiter):
		col = col.lower()
		result[col] = []
		colmapper[count] = col
		count += 1

	while 1:
		line = fp.readline()
		
		if not line:
			break
		
		line = line.strip()
		eachline = line.split(delimiter)
		
		for i in range(0, len(eachline)):
			lists = result[colmapper[i]]
			lists.append(eachline[i])
			result[colmapper[i]] = lists

	fp.close()
	
	with open("app/files/data_dump.pik", 'wb') as f:
		pickle.dump(result, f, -1)
	
	return "Dumped the file"

@app.route('/processgraphsyntax')
def processgraphsyntax():	
	graphsyntax = request.args.get('graphsyntax')
	graphsyntax = graphsyntax.strip()
	ds = None
	with open('app/files/data_dump.pik', 'rb') as f:
		ds = pickle.load(f)
	
	rules = graphsyntax.split(' ')
	graphtype = rules[0]
	graphtype = graphtype.lower()
	result = {}
	
	if graphtype not in ALLOWED_GRAPHTYPES:
		return jsonify({"ferror": "GraphType" + graphtype + " not supported. LINE, PIE, DONUT, SPLINE, AREA are the ones supported"})

	result["graphtype"] = graphtype

	for word in rules[1:]:
		word = word.lower()
		cols = word.split(":")
		
		if len(cols) == 2:
			result[cols[0]] = [cols[1]]
		else:
			result[cols[0]] = [cols[0]]
		
		lists = []

		if cols[0] in ds:
			for val in ds[cols[0]]:
				lists = result[cols[0]]
				lists.append(val)
			
			result[cols[0]] = lists
		else:
			result["error"] = "Column " + cols[0] + " not found in file"
			
	return jsonify(result)

